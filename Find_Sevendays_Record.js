db.CutDateTransform_Record.find(
    {
        cutDay: { $lt: "@cutday" },
        driver_id: "@driver_id",
        cutdatestarttime: { $ne: null }
    },
    {
        cutDay: 1,
        cutdatestarttime: 1,
        cutdateendtime: 1
    }
).sort({cutDay: -1}).limit(7)