#!/usr/bin/env python
"""Tests for `openstudio-backporter` package, from 3.9.0 to 3.8.0."""

from pathlib import Path

import openstudio

from openstudiobackporter import Backporter
from openstudiobackporter.helpers import get_objects_by_type

THIS_DIR = Path(__file__).parent / "3_8_0"


def backport_and_save(osm_rel_path: Path) -> openstudio.IdfFile:
    backporter = Backporter(to_version="3.7.0", save_intermediate=False)
    idf_file = backporter.backport_file(osm_path=THIS_DIR / osm_rel_path)
    new_name = f"output_{osm_rel_path.stem.replace('3_8_0', '3_7_0')}.osm"
    idf_file.save(THIS_DIR / new_name, True)

    # Ensure we can still load the backported file
    m_ = openstudio.model.Model.load(THIS_DIR / new_name)
    assert m_.is_initialized()

    return idf_file


def test_vt_HeatExchangerAirToAirSensibleAndLatent():
    idf_file = backport_and_save(osm_rel_path=Path("HeatExchangerAirToAirSensibleAndLatent_3_8_0.osm"))

    air_air_hxs = get_objects_by_type(
        idf_file=idf_file, idd_object_type_name="OS:HeatExchanger:AirToAir:SensibleAndLatent"
    )
    assert len(air_air_hxs) == 1
    air_air_hx = air_air_hxs[0]

    # Previous fields: Effectiveness at 100%
    assert air_air_hx.getDouble(4).get() == 0.8
    assert air_air_hx.getDouble(5).get() == 0.75
    assert air_air_hx.getDouble(8).get() == 0.8
    assert air_air_hx.getDouble(9).get() == 0.75

    # 4 deleted fields; 4 added fields
    assert air_air_hx.numFields() == 24

    # Additional old fields: Effectiveness at 75%
    assert air_air_hx.getDouble(6).get() == 0.8
    assert air_air_hx.getDouble(7).get() == 0.75
    assert air_air_hx.getDouble(10).get() == 0.8
    assert air_air_hx.getDouble(11).get() == 0.75


def test_vt_ZoneHVACPackagedTerminalAirConditioner():
    idf_file = backport_and_save(osm_rel_path=Path("ZoneHVACPackagedTerminalAirConditioner_3_8_0.osm"))

    ptacs = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:ZoneHVAC:PackagedTerminalAirConditioner")
    assert len(ptacs) == 1
    ptac = ptacs[0]

    #  1 deleted field
    assert ptac.numFields() == 18

    pthps = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:ZoneHVAC:PackagedTerminalHeatPump")
    assert len(pthps) == 1
    pthp = pthps[0]

    #  1 deleted field
    assert pthp.numFields() == 24


def test_vt_AirLoopHVACUnitarySystem():
    idf_file = backport_and_save(osm_rel_path=Path("AirLoopHVACUnitarySystem_3_8_0.osm"))

    u_syss = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:AirLoopHVAC:UnitarySystem")
    assert len(u_syss) == 1
    u_sys = u_syss[0]

    #  1 deleted field
    assert u_sys.numFields() == 40


def test_vt_PeopleDefinition():
    idf_file = backport_and_save(osm_rel_path=Path("PeopleDefinition_3_8_0.osm"))

    peoples = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:People:Definition")
    assert len(peoples) == 3

    for people in peoples:
        if value := people.getString(10):
            assert value.get() in ('ZoneAveraged', 'SurfaceWeighted')


def test_vt_ScheduleDay():
    idf_file = backport_and_save(osm_rel_path=Path("ScheduleDay_3_8_0.osm"))

    schedules = get_objects_by_type(idf_file=idf_file, idd_object_type_name="OS:Schedule:Day")
    assert len(schedules) == 3

    for schedule in schedules:
        if value := schedule.getString(3):
            assert value.get() in ('Yes', 'No', '')
