var cursor = db.Test.find(
    { driverId : "65" }
); 

var size = 0;
cursor.forEach(
    function(doc){
        size += bsonsize(doc);
    }
);

printjson(size);
