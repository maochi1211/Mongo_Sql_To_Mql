var cursor = db.Test.find(
    { driverId : "19264" }
); 

var size = 0;
cursor.forEach(
    function(doc){
        size += bsonsize(doc);
    }
);

printjson(size);
