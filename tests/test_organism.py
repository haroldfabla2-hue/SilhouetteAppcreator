"""Tests del organismo: homeostasis, ritmo circadiano y daemon vital.

La propiedad que más importa aquí es que **el organismo siga vivo pase lo que
pase**: un órgano que revienta no puede detener el latido. Eso es lo que separa
un organismo de un script programado.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from backend.app.organism.circadian import (
    PHASE_ENGINES,
    CircadianRhythm,
    Phase,
)
from backend.app.organism.homeostasis import (
    CADENCE_MULTIPLIER,
    EnvironmentState,
    Homeostasis,
    ResourceProfile,
)
from backend.app.organism.vital_daemon import (
    OrganismAlreadyRunning,
    VitalDaemon,
)


@pytest.fixture()
def daemon(tmp_path: Path) -> VitalDaemon:
    return VitalDaemon(
        state_path=tmp_path / "estado.json",
        lock_path=tmp_path / "organismo.lock",
        tick_interval_s=0.01,
    )


# ---------------------------------------------------------------------------
# Homeostasis
# ---------------------------------------------------------------------------
class TestHomeostasis:
    def test_mide_el_entorno_de_verdad(self) -> None:
        estado = Homeostasis().measure(force=True)
        assert 0.0 <= estado.ram_percent <= 100.0
        assert estado.cpu_count >= 1

    def test_la_presion_es_el_recurso_mas_saturado(self) -> None:
        estado = EnvironmentState(cpu_percent=30.0, ram_percent=95.0, disk_percent=50.0)
        assert estado.pressure == 95.0

    @pytest.mark.parametrize(
        "presion,esperado",
        [
            (99.0, ResourceProfile.CRITICAL),
            (85.0, ResourceProfile.CONSTRAINED),
            (60.0, ResourceProfile.BALANCED),
        ],
    )
    def test_clasifica_segun_la_presion(
        self, presion: float, esperado: ResourceProfile
    ) -> None:
        estado = EnvironmentState(ram_percent=presion, cpu_count=4, measured=True)
        perfil, motivo = Homeostasis().classify(estado)
        assert perfil is esperado
        assert motivo

    def test_ningun_perfil_desactiva_capacidades(self) -> None:
        """El principio del original: adaptar la cadencia, nunca perder capacidad."""
        for perfil in ResourceProfile:
            assert CADENCE_MULTIPLIER[perfil] > 0, (
                f"{perfil.value} anularía un motor en lugar de espaciarlo"
            )

    def test_bajo_presion_los_ciclos_se_espacian(self) -> None:
        h = Homeostasis()
        h.force_profile("critical")
        bajo_presion = h.adapt_interval(60.0)
        h.force_profile("abundant")
        holgado = h.adapt_interval(60.0)
        assert bajo_presion > holgado

    def test_el_intervalo_nunca_es_cero(self) -> None:
        h = Homeostasis()
        h.force_profile("abundant")
        assert h.adapt_interval(0.1) >= 1.0

    def test_sin_psutil_se_declara_no_medido(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import backend.app.organism.homeostasis as mod

        monkeypatch.setattr(mod, "PSUTIL_AVAILABLE", False)
        estado = Homeostasis().measure(force=True)
        # No inventa cifras: declara que no midió.
        assert estado.measured is False
        perfil, _ = Homeostasis().classify(estado)
        assert perfil is ResourceProfile.BALANCED

    def test_forzar_perfil_y_devolverlo_al_automatico(self) -> None:
        h = Homeostasis()
        h.force_profile("critical")
        assert h.is_forced
        assert h.synthesize().profile == "critical"
        h.force_profile(None)
        assert not h.is_forced

    def test_perfil_invalido_se_rechaza(self) -> None:
        with pytest.raises(ValueError, match="desconocido"):
            Homeostasis().force_profile("supersonico")


# ---------------------------------------------------------------------------
# Ritmo circadiano
# ---------------------------------------------------------------------------
class TestCircadiano:
    def test_arranca_despierto(self) -> None:
        assert CircadianRhythm().current().phase is Phase.ACTIVE

    def test_el_silencio_lleva_al_sueño(self) -> None:
        ritmo = CircadianRhythm()
        ritmo._last_interaction = time.time() - (2 * 3600)  # 2 h de silencio
        assert ritmo.current().phase is Phase.DREAMING

    def test_el_silencio_prolongado_lleva_al_reposo(self) -> None:
        ritmo = CircadianRhythm()
        ritmo._last_interaction = time.time() - (10 * 3600)
        assert ritmo.current().phase is Phase.DEEP_REST

    def test_interactuar_devuelve_a_la_vigilia(self) -> None:
        ritmo = CircadianRhythm()
        ritmo._last_interaction = time.time() - (5 * 3600)
        assert ritmo.current().phase is Phase.DEEP_REST
        ritmo.touch()
        assert ritmo.current().phase is Phase.ACTIVE

    def test_mientras_el_usuario_trabaja_el_organismo_se_aparta(self) -> None:
        """En ACTIVE sólo late: no compite por recursos con la petición."""
        ritmo = CircadianRhythm()
        estado = ritmo.current()
        assert estado.allows("heartbeat")
        assert not estado.allows("consolidation")
        assert not estado.allows("curiosity")

    def test_soñando_consolida_lo_aprendido(self) -> None:
        ritmo = CircadianRhythm()
        ritmo._last_interaction = time.time() - (2 * 3600)
        estado = ritmo.current()
        assert estado.allows("consolidation")
        assert estado.allows("curiosity")
        assert estado.allows("introspection")

    def test_todas_las_fases_laten(self) -> None:
        for fase, motores in PHASE_ENGINES.items():
            assert "heartbeat" in motores, f"{fase.value} dejaría de latir"

    def test_registra_las_transiciones(self) -> None:
        ritmo = CircadianRhythm()
        ritmo.current()
        ritmo._last_interaction = time.time() - (2 * 3600)
        ritmo.current()
        assert ritmo.transitions >= 1


# ---------------------------------------------------------------------------
# Daemon vital
# ---------------------------------------------------------------------------
class TestAislamientoDeFallos:
    async def test_un_organo_que_revienta_no_mata_al_organismo(
        self, daemon: VitalDaemon
    ) -> None:
        ejecutados: list[str] = []

        def organo_roto() -> None:
            raise RuntimeError("fallo catastrófico")

        def organo_sano() -> str:
            ejecutados.append("sano")
            return "ok"

        daemon.register("heartbeat", organo_roto, 0.001)
        daemon.register("vitals", organo_sano, 0.001)
        daemon.circadian._last_interaction = time.time() - 900  # fase DROWSY

        resultados = await daemon.tick()

        assert daemon.is_alive is False  # aún no se ha arrancado el bucle
        assert any(not r.ok for r in resultados), "el fallo debe registrarse"
        assert "sano" in ejecutados, "el resto de órganos debe seguir funcionando"

    async def test_el_organo_enfermo_se_marca_tras_fallos_seguidos(
        self, daemon: VitalDaemon
    ) -> None:
        def roto() -> None:
            raise ValueError("no")

        daemon.register("heartbeat", roto, 0.0)
        for _ in range(3):
            await daemon.tick()

        vitales = daemon.vitals()
        assert "heartbeat" in vitales["organs"]["unhealthy"]
        assert vitales["health"] in ("degraded", "critical")

    async def test_el_organismo_sobrevive_a_un_fallo_del_planificador(
        self, daemon: VitalDaemon
    ) -> None:
        # Un fallo al sintetizar la homeostasis no puede matar el bucle.
        def explota(*args: object, **kwargs: object) -> None:
            raise RuntimeError("homeostasis rota")

        daemon.homeostasis.synthesize = explota  # type: ignore[method-assign]
        daemon.start()
        await asyncio.sleep(0.05)
        assert daemon.is_alive, "el bucle vital debe seguir en marcha"
        await daemon.stop()

    async def test_el_error_se_registra_con_su_causa(self, daemon: VitalDaemon) -> None:
        def roto() -> None:
            raise KeyError("clave_ausente")

        daemon.register("heartbeat", roto, 0.0)
        await daemon.tick()
        organo = daemon._organs["heartbeat"]
        assert "KeyError" in organo.last_error


class TestVidaAutonoma:
    async def test_late_sin_que_nadie_interactue(self, daemon: VitalDaemon) -> None:
        """El bucle late por su cuenta, sin que nadie lo invoque.

        Se comprueba que el latido ocurre sin intervención; no se cuenta cuántos
        caben en una ventana de tiempo, porque bajo carga eso depende del
        planificador del sistema operativo y haría el test inestable.
        """
        latidos: list[float] = []
        daemon.register("heartbeat", lambda: latidos.append(time.time()), 0.0)

        daemon.start()
        # Espera activa acotada: en cuanto hay latido, se termina.
        for _ in range(200):
            if latidos:
                break
            await asyncio.sleep(0.01)
        await daemon.stop()

        assert latidos, "el organismo debe latir sin que nadie lo invoque"
        assert daemon.vitals()["ticks"] >= 1

    async def test_late_repetidamente(self, daemon: VitalDaemon) -> None:
        """El latido se repite: no es un disparo único de arranque."""
        latidos: list[float] = []
        daemon.register("heartbeat", lambda: latidos.append(time.time()), 0.0)

        for _ in range(3):
            await daemon.tick()

        assert len(latidos) == 3

    async def test_trabaja_mientras_nadie_mira(self, daemon: VitalDaemon) -> None:
        consolidaciones: list[int] = []
        daemon.register("consolidation", lambda: consolidaciones.append(1), 0.0)
        # Simular que nadie interactúa desde hace dos horas.
        daemon.circadian._last_interaction = time.time() - (2 * 3600)

        await daemon.tick()
        assert consolidaciones, "en fase de sueño debe consolidar memoria"

    async def test_se_aparta_cuando_el_usuario_trabaja(self, daemon: VitalDaemon) -> None:
        consolidaciones: list[int] = []
        daemon.register("consolidation", lambda: consolidaciones.append(1), 0.0)
        daemon.touch()  # interacción ahora mismo

        await daemon.tick()
        assert not consolidaciones, "no debe competir con la petición del usuario"

    async def test_admite_organos_asincronos(self, daemon: VitalDaemon) -> None:
        marcas: list[str] = []

        async def organo_async() -> str:
            await asyncio.sleep(0)
            marcas.append("async")
            return "listo"

        daemon.register("heartbeat", organo_async, 0.0)
        resultados = await daemon.tick()
        assert marcas == ["async"]
        assert resultados[0].ok

    async def test_respeta_la_cadencia_de_cada_organo(self, daemon: VitalDaemon) -> None:
        veces: list[int] = []
        daemon.register("heartbeat", lambda: veces.append(1), 3600.0)  # una vez por hora
        await daemon.tick()
        await daemon.tick()
        assert len(veces) == 1, "no debe reejecutarse antes de su intervalo"

    async def test_un_organo_desactivado_no_se_ejecuta(self, daemon: VitalDaemon) -> None:
        veces: list[int] = []
        daemon.register("heartbeat", lambda: veces.append(1), 0.0)
        daemon.set_enabled("heartbeat", False)
        await daemon.tick()
        assert veces == []


class TestPersistenciaYExclusion:
    async def test_el_ritmo_sobrevive_al_reinicio(self, tmp_path: Path) -> None:
        estado = tmp_path / "estado.json"
        lock = tmp_path / "org.lock"

        primero = VitalDaemon(state_path=estado, lock_path=lock, single_instance=False)
        primero.register("heartbeat", lambda: "ok", 0.0)
        await primero.tick()
        ejecuciones = primero._organs["heartbeat"].runs

        segundo = VitalDaemon(state_path=estado, lock_path=lock, single_instance=False)
        assert segundo._organs["heartbeat"].runs == ejecuciones
        assert segundo._organs["heartbeat"].last_run > 0

    def test_no_conviven_dos_organismos(self, tmp_path: Path) -> None:
        lock = tmp_path / "org.lock"
        primero = VitalDaemon(state_path=tmp_path / "a.json", lock_path=lock)
        primero._acquire_lock()

        segundo = VitalDaemon(state_path=tmp_path / "b.json", lock_path=lock)
        with pytest.raises(OrganismAlreadyRunning):
            segundo._acquire_lock()

        primero._release_lock()

    def test_un_bloqueo_huerfano_se_reclama(self, tmp_path: Path) -> None:
        lock = tmp_path / "org.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("999999", encoding="utf-8")  # PID que no existe

        daemon = VitalDaemon(state_path=tmp_path / "a.json", lock_path=lock)
        daemon._acquire_lock()  # no debe lanzar
        daemon._release_lock()


class TestSignosVitales:
    def test_reporta_su_estado(self, daemon: VitalDaemon) -> None:
        vitales = daemon.vitals()
        assert vitales["health"] == "healthy"
        assert "circadian" in vitales
        assert "homeostasis" in vitales
        assert vitales["organs"]["total"] >= 1

    async def test_la_tasa_de_fallo_es_real(self, daemon: VitalDaemon) -> None:
        daemon.register("heartbeat", lambda: "ok", 0.0)
        await daemon.tick()
        assert daemon.vitals()["activity"]["failure_rate"] == 0.0

    def test_sin_actividad_la_tasa_es_desconocida(self, daemon: VitalDaemon) -> None:
        # "Sin datos" es None, no 0.0 inventado.
        assert daemon.vitals()["activity"]["failure_rate"] is None

    async def test_arrancar_dos_veces_es_inocuo(self, daemon: VitalDaemon) -> None:
        daemon.start()
        daemon.start()
        assert daemon.is_alive
        await daemon.stop()
        assert not daemon.is_alive
