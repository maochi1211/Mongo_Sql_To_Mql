let collectionName = "cutdatetransformRecordNew";
let targetCollection = "trackRecord3New";

// 取得所有 driverId（不重複，字串格式）
function getAllDriverIds() {
    return db[collectionName].distinct("driverId").map(id => id.toString());
}

var driverIds = getAllDriverIds();

// 計算查詢範圍（cutday 用）
function getCutdayRange(date, pastDays) {
    let lastDay = new Date(date); // 目標日期
    lastDay.setUTCHours(0, 0, 0, 0);
    let firstDay = new Date(lastDay);
    firstDay.setDate(lastDay.getDate() - (pastDays - 1));
    let nextDay = new Date(lastDay);
    nextDay.setDate(nextDay.getDate() + 1);
    return [firstDay, nextDay];
}

// 改寫為 $lookup + unwind + group（v3）
function getDriveTimeV3(driverIds, date, pastDays) {
    const [startOfFirstDay, startOfDayAfterLast] = getCutdayRange(date, pastDays);

    print('startOfFirstDay:', startOfFirstDay.toISOString());
    print('startOfDayAfterLast:', startOfDayAfterLast.toISOString());

    return db[collectionName].aggregate([
        {
            $match: {
                driverId: { $in: driverIds.map(id => id.toString()) },
                cutday: { $gte: startOfFirstDay, $lt: startOfDayAfterLast }
            }
        },
        {
            $lookup: {
                from: targetCollection,
                let: {
                    lookup_driverId: "$driverId",
                    lookup_startOfDay: "$cutday",
                    lookup_endOfDayExclusive: { $add: [ "$cutday", 86400000 ] } // +1天 (毫秒)
                },
                pipeline: [
                    {
                        $match: {
                            $expr: {
                                $and: [
                                    { $eq: ["$realDrive", "$$lookup_driverId"] },
                                    { $gte: ["$startTime", "$$lookup_startOfDay"] },
                                    { $lt: ["$startTime", "$$lookup_endOfDayExclusive"] }
                                ]
                            }
                        }
                    },
                    { $project: { driveTime: 1, _id: 0 } }
                ],
                as: "dailyMatchedTracks"
            }
        },
        { $unwind: "$dailyMatchedTracks" },
        {
            $group: {
                _id: "$driverId",
                totalDriveTime: { $sum: "$dailyMatchedTracks.driveTime" }
            }
        },
        {
            $project: { _id: 0, driverId: "$_id", totalDriveTime: 1 }
        }
    ]).toArray();
}

// 使用範例
let date = new Date("2023-10-07");
let cursor = getDriveTimeV3(driverIds, date, 7);

// 顯示全部結果
if (cursor.length > 0) {
    cursor.forEach(function(record) {
        var total = record.totalDriveTime || 0;
        print(`Driver: ${record.driverId}, Total drive time: ${total}`);
    });
} else {
    print("No results found.");
}

// 查詢特定司機
let driverId = "65";
let singleResult = getDriveTimeV3([driverId], date, 7);
if (singleResult.length > 0) {
    print(`Single Driver ${driverId}:`);
    printjson(singleResult[0]);  // 
} else {
    print(`No data found for DriverId: ${driverId}`);
}