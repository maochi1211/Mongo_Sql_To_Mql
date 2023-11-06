use('Demo');

var currentDate = new Date();
var daysBefore = 7;
var currentDate = new Date(currentDate.getTime() - (daysBefore * 24 * 60 * 60 * 1000));
console.log('currentDate:', currentDate);

result = db.CutDateTransform_Record.find(
    {
        CutDateStartTime: { $lte: currentDate },
        CutDateEndTime: { $gte: currentDate }
    },
    {
        driver_id: 1,
        start_time: "$CutDateStartTime",
        end_time: "$CutDateEndTime",
        CutDay: 1
    }
);

var cnt = 0;
var driver_senvendays_list = [];

console.log('finding each driver seven days record...');

result.forEach(function(item) {
    cnt++;
    result = findDriverAndDate(item.CutDay, item.driver_id);
    driver_senvendays_list.push(result); 
});

console.log('Total number of driver ID:', cnt);
console.log('Driver seven days record:', driver_senvendays_list[0]);


function findDriverAndDate(cutDayValue, driverIdValue) {
    return db.CutDateTransform_Record.find(
            {
                CutDay: { $lt: cutDayValue },
                driver_id: driverIdValue,
                CutDateStartTime: { $ne: null }
            },
            {   
                driver_id: 1,
                CutDay: 1,
                CutDateStartTime: 1,
                CutDateEndTime: 1
            }
        ).sort({CutDay: -1}).limit(7)
};


