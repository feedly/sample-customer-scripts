let
    auth_token = "fe_zRiOc39tTBNbOTkcEAiV7I1iYqnwbYKL0L9ymcOq",
    stream_id = "enterprise/christeam/category/d53eb3d0-c5ba-471a-b484-eabc8f603711",
    epoch_time = Number.ToText(3 * -86400000), // minus three days in milliseconds
    count = "100",
    url = "https://feedly.com/v3/enterprise/ioc?streamid=" & stream_id & "&Count=" & count & "&newerThan=" & epoch_time,
    headers = [
        #"Authorization"= "Bearer " & auth_token,
        #"Content-Type"= "application/json"
    ],

    api_call = Web.Contents(url, [
        Headers = headers
    ]),

    json = Json.Document(api_call),
    data = json[objects],
    #"Converted to Table" = Table.FromList(data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Renamed Columns" = Table.RenameColumns(#"Converted to Table",{{"Column1", "Expanded"}}),
    #"Expanded" = Table.ExpandRecordColumn(#"Renamed Columns", "Expanded", {"type", "spec_version", "id", "created", "modified", "name", "description", "published", "object_refs", "external_references", "pattern", "pattern_type", "pattern_version", "valid_from"}, {"type", "spec_version", "id", "created", "modified", "name", "description", "published", "object_refs", "external_references", "pattern", "pattern_type", "pattern_version", "valid_from"}),
    #"Expanded object_refs" = Table.ExpandListColumn(Expanded, "object_refs"),
    #"Expanded external_references" = Table.ExpandListColumn(#"Expanded object_refs", "external_references"),
    #"Expanded external_references1" = Table.ExpandRecordColumn(#"Expanded external_references", "external_references", {"source_name", "url"}, {"source_name", "url"})
in
    #"Expanded external_references1"