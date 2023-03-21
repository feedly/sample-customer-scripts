## This PowerShell script can be used to ingest IoCs from a Folder, AI Feed (formerly Leo Web Alert), or Board you want to access
## Refer to the following guide on how to generate a stream ID: https://feedly.notion.site/Hello-IoCs-Fetch-IoCs-with-rich-context-57d18674fc75499498c3e0546dba1225
## The response will be a STIX JSON containing a bundle with all the IoCs, context (threat actors, malware families, CVEs), and their relationships

$stream_id = "YOUR STREAM ID"
$token = "YOUR API KEY"
$universal_time_last_day = (Get-Date).AddHours(-24).ToUniversalTime() # Generates a timestamp for 24 hours prior to the current date
$epoch_time_last_day = ([System.DateTimeOffset]$universal_time_last_day).ToUnixTimeSeconds()
$count = 10 # Can be set to a maximum of 100 before you need to enable continuation

$headers = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
$headers.Add("Authorization", "Bearer $token")
$url_string = "https://feedly.com/v3/enterprise/ioc?streamid=$stream_id&newerThan=$epoch_time_last_day&Count=$count"
$response = Invoke-RestMethod $url_string -Method "GET" -Headers $headers
$response | ConvertTo-Json -Depth 10 | Out-File -FilePath ".\feedly_ioc_extraction_output.json"