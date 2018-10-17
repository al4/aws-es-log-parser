aws-es-slow-log-parser
======================

A very dirty and not particularly quick AWS Elasticsearch slow log parser.

It's horrible single-use code, and not intended for use by anyone else!

Most of the logic is trying to make truncated JSON documents valid.

Example
-------

Download the logs from Cloudwatch to a file:
```sh
GROUPNAME=/aws/aes/domains/blue-demo/index-logs
aws logs describe-log-streams --log-group-name $GROUPNAME | \
    jq '.logStreams[] | .logStreamName' | \
    xargs -I {} aws logs get-log-events --log-group-name $GROUPNAME --log-stream-name {} | \
    jq '.events[]' > logfile
```

Entries in logfile should look similar to:
```json
{
  "timestamp": 1539711398789,
  "message": "[2018-10-16T10:36:38,174][DEBUG][index.indexing.slowlog.index] ...",
  "ingestionTime": 1539711404055
}
```

Run them through this script:
```sh
jq '.message' < logfile | python3 parse_awses_slowlogs.py --log-level warn out.txt
```
out.txt should then contain lines of parsable JSON.

Using `--log-level info` will show you stats on lines that failed to parse.
`--log-level debug` probably won't help you much if that number is too high.
