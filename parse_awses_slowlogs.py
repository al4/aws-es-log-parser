import json
import sys

UNTERMINATED = "Unterminated string"
EXPECTING_OBJECT = "Expecting object"
EXPECTING_COLON = "Expecting : delimiter"
EXPECTING_PROPERTY = "Expecting property name:"
OOB = "end is out of bounds"
EXPECTING_COMMA = "Expecting , delimiter"
NO_JSON = "No JSON object could be decoded"


def parse_truncated_json(s, depth=0, last_error=None):
    print(s)
    if depth > 10:
        raise Exception("Too deep for string {}, last error: {}".format(
            s, last_error))
    try:
        o = json.loads(s)
    except ValueError as e:
        # print('string {} gives {}'.format(s, e.args[0]))
        err = parse_error(e.args[0])
        print('err: {}'.format(err))

        depth += 1
        if err == UNTERMINATED:
            if last_error == err:
                s = s + '}'
            else:
                s = s + '"'
        elif find_open_bracket(s):
            c = find_open_bracket(s)
            if c:
                s = s + c
        elif err == EXPECTING_OBJECT:
            if s[-1:] == ',':
                s = s[:-1]
            else:
                s = s + '}'
        elif err == EXPECTING_COLON:
            s = s + ':""'
        elif err == EXPECTING_PROPERTY and s[-1:].isalnum():
            s = s + '"}'
        elif err == OOB and s[-2:] == ',"':
            s = s[:-2]
        elif err == OOB and s[-1:] == '"':
            s = s[:-1]
        elif err == OOB and s[-1:] == ':':
            s = s + '""'
        elif err == EXPECTING_COMMA:
            c = find_open_bracket(s)
            if c:
                s = s + c
        elif err == NO_JSON:
            s = s[:-1]
        else:
            raise Exception("Failed to parse string '{}': {}".format(
                s, e.args[0]))
        return parse_truncated_json(s, depth, last_error=OOB)
    return o


def find_open_bracket(s):
    lsb = s.rfind('[')
    rsb = s.rfind(']')
    if lsb and (not rsb or lsb > rsb):
        sb_append = ']'
    else:
        sb_append = None

    lbr = s.rfind('{')
    rbr = s.rfind('}')
    if lbr and (not rbr or lbr > rbr):
        br_append = '}'
    else:
        br_append = None

    if lbr > lsb:
        return br_append
    else:
        return sb_append


def parse_error(msg):
    if UNTERMINATED in msg:
        return UNTERMINATED
    if EXPECTING_OBJECT in msg:
        return EXPECTING_OBJECT
    if EXPECTING_COLON in msg:
        return EXPECTING_COLON
    if EXPECTING_PROPERTY in msg:
        return EXPECTING_PROPERTY
    if OOB in msg:
        return OOB
    if EXPECTING_COMMA in msg:
        return EXPECTING_COMMA
    if NO_JSON in msg:
        return NO_JSON
    return None


def find_field(s, name='source'):
    x = line.find('{}['.format(name)) + len(name) + 1
    try:
        y = line.index(']"', x)
    except ValueError:
        pass
    try:
        y = line.index(']', x)
    except ValueError:
        return None

    return line[x:y]


failed = 0
succeeded = 0
for line in sys.stdin.readlines():
    # print("---- line {}".format(1 + failed + succeeded))
    # print(line)
    source = find_field(line, name='source')
    # print("Source: {}".format(source))
    took = find_field(line, name='took')
    # print("Took: {}".format(took))

    if not all((source, took)):
        print("Skipping message '{}'".format(line))
        continue

    source = source.replace('\\"', '"')
    try:
        o = parse_truncated_json(source)
    except Exception as e:
        failed += 1
        print("Failed to parse line; Error: {}; line: {}".format(
            e.args[0], line))
        continue
    succeeded += 1
    # print(o)

print("S: {}; F: {}".format(succeeded, failed))
