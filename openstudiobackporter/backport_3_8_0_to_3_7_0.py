import openstudio
from loguru import logger

from openstudiobackporter.helpers import (
    brief_description,
    copy_object_as_is,
    copy_with_added_fields,
    copy_with_deleted_fields,
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
            copy_from_indices = (4, 5, 6, 7)
            copy_to_indices = (6, 7, 10, 11)
            copy_with_added_fields(obj=obj, newObject=newObject, skip_indices=copy_to_indices)
            for cf, ct in zip(copy_from_indices, copy_to_indices):
                if value := obj.getString(cf):
                    newObject.setString(ct, value.get())
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
            copy_with_deleted_fields(obj=obj, newObject=newObject, skip_indices={10})
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
