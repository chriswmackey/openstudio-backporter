import openstudio
from loguru import logger

from openstudiobackporter.helpers import (
    brief_description,
    copy_object_as_is,
    copy_with_added_fields,
    copy_with_deleted_fields
)


def run_translation(idf_3_8_0: openstudio.IdfFile) -> openstudio.IdfFile:
    """Backport an IdfFile from 3.8.0 to 3.7.0."""
    logger.info("Backporting from 3.8.0 to 3.7.0")

    idd_3_7_0 = (
        openstudio.IddFactory.instance()
        .getIddFile(openstudio.IddFileType("OpenStudio"), openstudio.VersionString(3, 7, 0))
        .get()
    )
    targetIdf = openstudio.IdfFile(idd_3_7_0)

    for obj in idf_3_8_0.objects():
        iddname = obj.iddObject().name()

        iddObject_ = idd_3_7_0.getObject(iddname)
        if not iddObject_.is_initialized():  # pragma: no cover
            # Object type doesn't exist in target version, skip it (None in 3.8.0 to 3.7.0 backport)
            logger.warning(f"{brief_description(idf_obj=obj)} does not exist in version 3.7.0, skipping.")
            continue

        iddObject = iddObject_.get()
        newObject = openstudio.IdfObject(iddObject)

        if iddname == "OS:HeatExchanger:AirToAir:SensibleAndLatent":

            # 4 Fields have been removed from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Sensible Effectiveness at 75% Heating Air Flow {dimensionless} * 6
            # * Latent Effectiveness at 75% Heating Air Flow {dimensionless} * 7
            # * Sensible Effectiveness at 75% Cooling Air Flow {dimensionless} * 10
            # * Latent Effectiveness at 75% Cooling Air Flow {dimensionless} * 11

            # 4 Fields have been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Sensible Effectiveness of Heating Air Flow Curve Name * 20
            # * Latent Effectiveness of Heating Air Flow Curve Name * 21
            # * Sensible Effectiveness of Cooling Air Flow Curve Name * 22
            # * Latent Effectiveness of Cooling Air Flow Curve Name * 23

            # copy the object while inserting fields for the Effectiveness at 75%
            eff_75_indices = (6, 7, 10, 11)
            eff_100_indices = (4, 5, 6, 7)
            eff_curve_indices = (20, 21, 22, 23)
            copy_with_added_fields(obj=obj, newObject=newObject, inserted_indices=set(eff_75_indices))

            # loop through the effectiveness curves and convert them
            for e100, e75, ec in zip(eff_100_indices, eff_75_indices, eff_curve_indices):
                curve_id = openstudio.toUUID(obj.getField(ec).get())
                curve_obj = idf_3_8_0.getObject(curve_id)
                if curve_obj:
                    curve_obj = curve_obj.get()
                    curve_idd_name = curve_obj.iddObject().name()
                    if curve_idd_name == "OS:Table:Lookup":  # pull the value from the table
                        if e75_value := curve_obj.getDouble(11):
                            newObject.setDouble(e75, e75_value.get())
                    elif curve_idd_name == "OS:Curve:Quadratic":  # reverse translate the curve and evaluate it
                        # collect all of the objects the curve references
                        temp_model = openstudio.model.Model()
                        hx_curve = openstudio.model.CurveQuadratic(temp_model)
                        if coeff_value := curve_obj.getDouble(2):
                            hx_curve.setCoefficient1Constant(coeff_value.get())
                        if coeff_value := curve_obj.getDouble(3):
                            hx_curve.setCoefficient2x(coeff_value.get())
                        if coeff_value := curve_obj.getDouble(4):
                            hx_curve.setCoefficient3xPOW2(coeff_value.get())
                        if e100_value := obj.getDouble(e100):
                            e100_value = e100_value.get()
                            print(hx_curve.evaluate(0.75) * e100_value)
                            newObject.setDouble(e75, hx_curve.evaluate(0.75) * e100_value)

                else:  # if no curve has been assigned, assume a constant effectiveness
                    if value := obj.getString(e100):
                        newObject.setString(e75, value.get())

            targetIdf.addObject(newObject)

        elif (
            iddname == "OS:ZoneHVAC:PackagedTerminalAirConditioner" or iddname == "OS:ZoneHVAC:PackagedTerminalHeatPump"
        ):

            # 1 Field has been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * No Load Supply Air Flow Rate Control Set To Low Speed * 10
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={10})
            targetIdf.addObject(newObject)

        elif iddname == "OS:ZoneHVAC:WaterToAirHeatPump":

            # 1 Field has been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * No Load Supply Air Flow Rate Control Set To Low Speed * 9
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={9})
            targetIdf.addObject(newObject)

        elif iddname == "OS:AirLoopHVAC:UnitarySystem":

            # 1 Field has been added from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * No Load Supply Air Flow Rate Control Set To Low Speed * 35
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={35})
            targetIdf.addObject(newObject)

        elif iddname == "OS:People:Definition":

            # 1 Key has been changed from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Mean Radiant Temperature Calculation Type * 10
            #   * ZoneAveraged -> EnclosureAveraged
            copy_object_as_is(obj=obj, newObject=newObject)
            if value := obj.getString(10):
                value = value.get()
                value = 'ZoneAveraged' if value == 'EnclosureAveraged' else value
                newObject.setString(10, value)
            targetIdf.addObject(newObject)

        elif iddname == "OS:Schedule:Day":

            # 1 Field has been modified from 3.7.0 to 3.8.0:
            # ----------------------------------------------
            # * Interpolate to Timestep * 3 - Changed from bool to string choice
            copy_object_as_is(obj=obj, newObject=newObject)
            if value := obj.getString(3):
                value = value.get()
                value = 'Yes' if value not in ('No', '') else value
                newObject.setString(3, value)
            targetIdf.addObject(newObject)

        else:
            copy_object_as_is(obj=obj, newObject=newObject)
            targetIdf.addObject(newObject)

    return targetIdf
