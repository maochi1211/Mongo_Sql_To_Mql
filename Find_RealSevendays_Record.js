let collectionName = "cutdatetransformRecordNew";

// 函數：取得所有不重複的 driverId（確保轉為字串）
function getAllDriverIds() {
    return db[collectionName].distinct("driverId").map(id => id.toString());
}

var driverIds = getAllDriverIds();

// 函數：取得某個 driverId 在某個日期之前的所有紀錄
function getDriveTime(driverIds, date, pastDays) {
    let endOfDay = new Date(date);
    endOfDay.setUTCHours(23, 59, 59, 999); // 設定為當日結束 (UTC+8)

    let startOfDay = new Date(date);
    startOfDay.setDate(startOfDay.getDate() - (pastDays - 1)); // pastDays 天前
    startOfDay.setUTCHours(0, 0, 0, 0); // 設定為當日開始 (UTC+8)

    console.log('startOfDay:', startOfDay.toISOString());
    console.log('endOfDay:', endOfDay.toISOString());

    return db[collectionName].aggregate([
        {
            $match: {
                driverId: { $in: driverIds.map(id => id.toString()) }  // 確保 driverId 是字串
            }
        },
        {
            $unwind: "$trackRecord3News"
        },
        {
            $match: {
                "trackRecord3News.startTime": { $gte: startOfDay, $lt: endOfDay }
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

// 目標日期
var date = new Date('2023-10-07'); 
var n = 0;
var cursor = getDriveTime(driverIds, date, 7);

// 確保 cursor 內有資料才進行迴圈
if (cursor.length > 0) {
    cursor.forEach(function(record) {
        var totalDriveTime = record.totalDriveTime ? record.totalDriveTime : 0;
        console.log('Driver ID:', record._id, 'Total drive time:', totalDriveTime);
        n++;
    });
} else {
    console.log("No records found!");
}

console.log('Driver IDs:', driverIds);
console.log('===============');
console.log('Total number of drivers:', n);
console.log('===============');

// 指定特定 driver 計算七天內總駕駛時間
let specificDriverId = "65";
let cursor2 = getDriveTime([specificDriverId], date, 7);

if (cursor2.length > 0) {
    var totalDriveTime2 = cursor2[0].totalDriveTime || 0;
    console.log('DriverId:', specificDriverId);
    console.log('Total drive time:', totalDriveTime2);
    printjson(cursor2[0]);
} else {
    console.log(`No data found for DriverId: ${specificDriverId}`);
}
