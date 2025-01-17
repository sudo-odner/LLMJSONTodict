import json

from LLMJSONDecoder import custom_json_load

# from LLMJSONToDict2 import LLMJSONDecoder

mocks = [
    """
    {some: 1, some: []}
    """,
    """
    {
        some: 1,
        some: {other: 2},
        some: 23
    }
    """,
    """
    {some: 1, some: {other: 2}, other: {other: 3}}
    """,
    """
    """,
    """
    {"test": 1, "test2": 2}
    """,
    """
    {"test": {d: 4, f:3}, "test2": 2}
    """,
    """
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {},
          "geometry": {
            "type": "Point",
            "coordinates": [4.483605784808901, 51.907188449679325]
          }
        },
        {
          "type": "Feature",
          "properties": {},
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [3.974369110811523 , 51.907355547778565],
                [4.173944459020191 , 51.86237166892457 ],
                [4.3808076710679416, 51.848867725914914],
                [4.579822414365026 , 51.874487141880024],
                [4.534413416598767 , 51.9495302480326  ],
                [4.365110733567974 , 51.92360787140825 ],
                [4.179550508127079 , 51.97336560819281 ],
                [4.018096293847009 , 52.00236546429852 ],
                [3.9424146309028174, 51.97681895676649 ],
                [3.974369110811523 , 51.907355547778565]
              ]
            ]
          }
        }
      ]
    }
    """,
    """
    {
        "type": "Feature", // this is comment
        "properties": {},
        "geometry": { // this is comment
            "type": "Point",
            "coordinates": [4.483605784808901, 51.907188449679325]
    }
    """,
    """
{
    "type": "Feature", // this is comment
    "properties": {},
    "geometry": { // this is comment
        "type": "Point",
        "coordinates": [4.483605784808901, 51.907188449679325]
}}
""",
    """
{
    "address": ["124241,  Feature"], // this is comment
    properties: {},
    "geometry": { // this is comment
        "type": "Point", // this is comment
        "coordinates": [4.483605784808901,   51.907188449679325]
    }
}
    """,
    """
{
    "address": ["124241,  '// this is not comment, Feature"], // this is comment
    "properties": {},
    "geometry": { // this is comment
        "type": "Point", // this is comment
        "coordinates": [4.483605784808901,   51.907188449679325]
    }
}
    """,
    """{
"person": [{
"LastName": "Хорошков",
"firstName": "Никита",
"middleName": "Олегович",
"jobTitle": "Генеральный Директор"
}]
}
    """,
    """{/*
"person": [{
"LastName": "Хорошков",
"firstName": "Никита",*/
"middleName": "Олегович",
"jobTitle": "Генеральный Директор"
}]
}
    """
]

# print(mocks[-6])
# print(custom_json_load(mocks[-6]))

for mock in mocks:
    print(mock)
    print(custom_json_load(mock))