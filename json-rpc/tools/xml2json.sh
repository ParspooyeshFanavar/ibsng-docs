python xml2json.py ../handlers_E.xml E ..
python xml2json.py ../handlers_D.xml D ..
python xml2json.py ../handlers_C.xml C ..

cd format-json
go build
./format-json ../../*/*.json