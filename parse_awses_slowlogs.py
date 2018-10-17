import json
import sys

UNTERMINATED = "Unterminated string"
EXPECTING_OBJECT = "Expecting object"
EXPECTING_COLON = "Expecting : delimiter"
EXPECTING_PROPERTY = "Expecting property name:"
OOB = "end is out of bounds"


def parse_truncated_json(s, depth=0, last_error=None):
    if depth > 3:
        raise Exception("Too deep, last error was: {}".format(last_error))
    try:
        o = json.loads(s)
    except ValueError as e:
        # print('string {} gives {}'.format(s, e.args[0]))
        err = parse_error(e.args[0])

        depth += 1
        if err == UNTERMINATED:
            if last_error == err:
                s = s + '}'
            else:
                s = s + '"'
        elif err == EXPECTING_OBJECT:
            if s[-1:] == ',':
                s = s[:-1]
            else:
                s = s + '}'
        elif err == EXPECTING_COLON:
            s = s + ':""'
        elif err == EXPECTING_PROPERTY and s[-1:].isalnum():
            # s = s + ':""'
            s = s + '"}'
        elif err == OOB and s[-2:] == ',"':
            s = s[:-2]
        return parse_truncated_json(s, depth, last_error=OOB)

        raise Exception("Don't know how to deal with this")
    return o


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
            e.args[0], source))
        continue
    succeeded += 1
    # print(o)
