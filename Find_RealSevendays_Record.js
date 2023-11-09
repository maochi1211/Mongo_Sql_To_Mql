// 函數：取得所有不重複的 driverId
function getAllDriverIds() {
    // 使用 distinct 方法找出所有不重複的 driverId
    return db.cutDateTransformRecordNew.distinct("driverId");
}

var driverIds = getAllDriverIds();

console.log('Driver IDs:', driverIds);
console.log('===============');

// 函數：取得某個 driverId 在某個日期之前的所有紀錄
function getDriveTime(driverIds, date, pastDays) {
    let endOfDay = new Date(date);
    endOfDay.setUTCHours(23, 59, 59, 999); // UTC+8

    let startOfDay = new Date(date);
    startOfDay.setDate(startOfDay.getDate() - (pastDays-1)); // pastDays days before
    startOfDay.setUTCHours(0, 0, 0, 0); // UTC+8

    console.log('startOfDay:', startOfDay);
    console.log('endOfDay:', endOfDay);

    return db.cutDateTransformRecordNew.aggregate([
        {
            $match: {
                driverId: { $in: driverIds }
            }
        },
        {
            $unwind: "$trackRecord3News"
        },
        {
            $match: {
                "trackRecord3News.startTime": {
                    $gte: startOfDay
                },
                "trackRecord3News.endTime": {
                    $lt: endOfDay
                }
            }
        },
        {
            $group: {
                _id: "$driverId",
                totalDriveTime: { $sum: "$trackRecord3News.driveTime" }
            }
        }
    ]).toArray();
}

var date = new Date('2023-10-07')
cursor = getDriveTime(driverIds, date, 7)
cursor.forEach(function(record) {
    var totalDriveTime = record.totalDriveTime ? record.totalDriveTime : 0;
    console.log('Driver ID:', record._id, 'Total drive time:', totalDriveTime);
});

console.log('===============');

var date = new Date('2023-10-07')
cursor2 = getDriveTime(['87'], date=date, pastDays=7)
var totalDriveTime2 = cursor2.totalDriveTime ? cursor2.totalDriveTime : 0;
console.log('Total drive time:', totalDriveTime2);
printjson(cursor2);


