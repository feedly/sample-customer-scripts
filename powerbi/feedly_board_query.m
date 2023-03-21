// Feedly Board Query (given a board stream ID)
// Returns JSON with details of each article in the range specified by the count and newerThan parameters
let
    auth_token = "YOUR API KEY",
    stream_id = "YOUR BOARD STREAM ID",
		// You can specifify a newerThan field, but this is disabled in this current example
    // epoch_time = "-86400",
    count = "5", // The number of articles you want to return
    url = "https://feedly.com/v3/streams/contents?streamid=" & stream_id & "&Count=" & count, // "&newerThan=" & epoch_time,

    headers = [
        #"Authorization"= "Bearer " & auth_token,
        #"Content-Type"= "application/json"
    ],

    api_call = Web.Contents(url, [
        Headers = headers
    ]),

    json = Json.Document(api_call),
    data = json[items],
		// The following table transformations will expand the nested record fields into new lines
    #"Converted to Table" = Table.FromList(data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Expanded Column1" = Table.ExpandRecordColumn(#"Converted to Table", "Column1", {"fingerprint", "language", "id", "keywords", "originId", "authorDetails", "origin", "title", "author", "crawled", "published", "canonical", "summary", "alternate", "visual", "expandedInline", "unread", "annotations", "categories", "tags", "commonTopics", "entities", "linked", "leoSummary", "indicatorsOfCompromise", "actionTimestamp", "engagement", "sources", "updated", "canonicalUrl", "fullContent", "recrawled", "updateCount", "content", "attackNavigator", "thumbnail"}, {"fingerprint", "language", "id", "keywords", "originId", "authorDetails", "origin", "title", "author", "crawled", "published", "canonical", "summary", "alternate", "visual", "expandedInline", "unread", "annotations", "categories", "tags", "commonTopics", "entities", "linked", "leoSummary", "indicatorsOfCompromise", "actionTimestamp", "engagement", "sources", "updated", "canonicalUrl", "fullContent", "recrawled", "updateCount", "content", "attackNavigator", "thumbnail"}),
    #"Expanded keywords" = Table.ExpandListColumn(#"Expanded Column1", "keywords"),
    #"Expanded authorDetails" = Table.ExpandRecordColumn(#"Expanded keywords", "authorDetails", {"source", "url", "username"}, {"source", "url", "username"}),
    #"Expanded origin" = Table.ExpandRecordColumn(#"Expanded authorDetails", "origin", {"title", "streamId", "htmlUrl"}, {"title.1", "streamId", "htmlUrl"}),
    #"Expanded canonical" = Table.ExpandListColumn(#"Expanded origin", "canonical"),
    #"Expanded canonical1" = Table.ExpandRecordColumn(#"Expanded canonical", "canonical", {"href", "type"}, {"href", "type"}),
    #"Expanded summary" = Table.ExpandRecordColumn(#"Expanded canonical1", "summary", {"content", "direction"}, {"content.1", "direction"}),
    #"Expanded visual" = Table.ExpandRecordColumn(#"Expanded summary", "visual", {"processor", "contentType", "url", "width", "height", "expirationDate", "edgeCacheUrl"}, {"processor", "contentType", "url.1", "width", "height", "expirationDate", "edgeCacheUrl"}),
    #"Expanded annotations" = Table.ExpandListColumn(#"Expanded visual", "annotations"),
    #"Expanded annotations1" = Table.ExpandRecordColumn(#"Expanded annotations", "annotations", {"author", "authorFirstInitial", "created", "entryId", "highlight", "id", "comment", "emailMentions", "slackMentions"}, {"author.1", "authorFirstInitial", "created", "entryId", "highlight", "id.1", "comment", "emailMentions", "slackMentions"}),
    #"Expanded highlight" = Table.ExpandRecordColumn(#"Expanded annotations1", "highlight", {"version", "start", "end", "text"}, {"version", "start", "end", "text"}),
    #"Expanded emailMentions" = Table.ExpandListColumn(#"Expanded highlight", "emailMentions"),
    #"Expanded slackMentions" = Table.ExpandListColumn(#"Expanded emailMentions", "slackMentions"),
    #"Expanded categories" = Table.ExpandListColumn(#"Expanded slackMentions", "categories"),
    #"Expanded categories1" = Table.ExpandRecordColumn(#"Expanded categories", "categories", {"id", "label"}, {"id.2", "label"}),
    #"Expanded tags" = Table.ExpandListColumn(#"Expanded categories1", "tags"),
    #"Expanded tags1" = Table.ExpandRecordColumn(#"Expanded tags", "tags", {"id", "label", "addedBy", "actionTimestamp"}, {"id.3", "label.1", "addedBy", "actionTimestamp.1"}),
    #"Expanded commonTopics" = Table.ExpandListColumn(#"Expanded tags1", "commonTopics"),
    #"Expanded commonTopics1" = Table.ExpandRecordColumn(#"Expanded commonTopics", "commonTopics", {"type", "id", "label", "score", "salienceLevel"}, {"type.1", "id.4", "label.2", "score", "salienceLevel"}),
    #"Expanded entities" = Table.ExpandListColumn(#"Expanded commonTopics1", "entities"),
    #"Expanded entities1" = Table.ExpandRecordColumn(#"Expanded entities", "entities", {"type", "disambiguated", "id", "label", "mentions", "salienceLevel"}, {"type.2", "disambiguated", "id.5", "label.3", "mentions", "salienceLevel.1"}),
    #"Expanded mentions" = Table.ExpandListColumn(#"Expanded entities1", "mentions"),
    #"Expanded mentions1" = Table.ExpandRecordColumn(#"Expanded mentions", "mentions", {"text"}, {"text.1"}),
    #"Expanded linked" = Table.ExpandListColumn(#"Expanded mentions1", "linked"),
    #"Expanded linked1" = Table.ExpandRecordColumn(#"Expanded linked", "linked", {"language", "id", "parentEntryId", "title", "content", "author", "crawled", "summary", "alternate", "enclosure", "visual", "canonicalUrl", "ampUrl", "cdnAmpUrl", "expandedInline", "unread", "categories", "commonTopics", "entities", "leoSummary", "indicatorsOfCompromise", "attackNavigator"}, {"language.1", "id.6", "parentEntryId", "title.2", "content.2", "author.2", "crawled.1", "summary", "alternate.1", "enclosure", "visual", "canonicalUrl.1", "ampUrl", "cdnAmpUrl", "expandedInline.1", "unread.1", "categories", "commonTopics", "entities", "leoSummary.1", "indicatorsOfCompromise.1", "attackNavigator.1"}),
    #"Expanded summary1" = Table.ExpandRecordColumn(#"Expanded linked1", "summary", {"content"}, {"content.3"}),
    #"Expanded alternate.1" = Table.ExpandListColumn(#"Expanded summary1", "alternate.1"),
    #"Expanded alternate.2" = Table.ExpandRecordColumn(#"Expanded alternate.1", "alternate.1", {"href", "type"}, {"href.1", "type.3"}),
    #"Expanded enclosure" = Table.ExpandListColumn(#"Expanded alternate.2", "enclosure"),
    #"Expanded enclosure1" = Table.ExpandRecordColumn(#"Expanded enclosure", "enclosure", {"href", "type"}, {"href.2", "type.4"}),
    #"Expanded visual1" = Table.ExpandRecordColumn(#"Expanded enclosure1", "visual", {"url"}, {"url.2"}),
    #"Expanded categories2" = Table.ExpandListColumn(#"Expanded visual1", "categories"),
    #"Expanded categories3" = Table.ExpandRecordColumn(#"Expanded categories2", "categories", {"id", "label"}, {"id.7", "label.4"}),
    #"Expanded commonTopics2" = Table.ExpandListColumn(#"Expanded categories3", "commonTopics"),
    #"Expanded commonTopics3" = Table.ExpandRecordColumn(#"Expanded commonTopics2", "commonTopics", {"type", "id", "label", "score", "causes", "salienceLevel"}, {"type.5", "id.8", "label.5", "score.1", "causes", "salienceLevel.2"}),
    #"Expanded causes" = Table.ExpandListColumn(#"Expanded commonTopics3", "causes"),
    #"Expanded causes1" = Table.ExpandRecordColumn(#"Expanded causes", "causes", {"id", "label"}, {"id.9", "label.6"}),
    #"Expanded entities2" = Table.ExpandListColumn(#"Expanded causes1", "entities"),
    #"Expanded entities3" = Table.ExpandRecordColumn(#"Expanded entities2", "entities", {"type", "disambiguated", "id", "label", "mentions", "salienceLevel"}, {"type.6", "disambiguated.1", "id.10", "label.7", "mentions", "salienceLevel.3"}),
    #"Expanded mentions2" = Table.ExpandListColumn(#"Expanded entities3", "mentions"),
    #"Expanded mentions3" = Table.ExpandRecordColumn(#"Expanded mentions2", "mentions", {"text"}, {"text.2"}),
    #"Expanded leoSummary.1" = Table.ExpandRecordColumn(#"Expanded mentions3", "leoSummary.1", {"sentences"}, {"sentences"}),
    #"Expanded sentences" = Table.ExpandListColumn(#"Expanded leoSummary.1", "sentences"),
    #"Expanded sentences1" = Table.ExpandRecordColumn(#"Expanded sentences", "sentences", {"text", "position", "score"}, {"text.3", "position", "score.2"}),
    #"Expanded indicatorsOfCompromise.1" = Table.ExpandRecordColumn(#"Expanded sentences1", "indicatorsOfCompromise.1", {"mentions", "exports"}, {"mentions", "exports"}),
    #"Expanded mentions4" = Table.ExpandListColumn(#"Expanded indicatorsOfCompromise.1", "mentions"),
    #"Expanded mentions5" = Table.ExpandRecordColumn(#"Expanded mentions4", "mentions", {"text", "type", "canonical"}, {"text.4", "type.7", "canonical"})
in
    #"Expanded mentions5"