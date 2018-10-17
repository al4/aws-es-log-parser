#!/usr/bin/env python3
import argparse
import json
import re
import sys
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

EXPECTING_COLON = "Expecting ':' delimiter"
EXPECTING_COMMA = "Expecting ',' delimiter"
EXPECTING_OBJECT = "Expecting object"
EXPECTING_PROPERTY = "Expecting property name"
EXPECTING_VALUE = "Expecting value:"
NO_JSON = "No JSON object could be decoded"
OOB = "end is out of bounds"
UNTERMINATED = "Unterminated string"


def parse_truncated_json(s, depth=0, last_error=None):
    if depth > 10:
        raise Exception("Too deep for string {}, last error: {}".format(
            s, last_error))
    try:
        o = json.loads(s)
    except (ValueError, json.decoder.JSONDecodeError) as e:
        err, col = parse_error(e.args[0])
        log.debug('string: `{}`; err `{}`; last: `{}`'.format(
            s, e.args[0], last_error))
        depth += 1

        log.debug("len: {}, col: {}".format(len(s), col))
        print("FOO", s[-1:], err)

        if err is UNTERMINATED:
            s = s + '"'
        elif err is EXPECTING_PROPERTY and s[-1:].isalnum():
            s = s + '"}'
        elif err is EXPECTING_PROPERTY and s[-1:] == ',':
            print('BAR')
            s = s[:-1]
        elif err is OOB and s[-2:] == ',"':
            s = s[:-2]
        elif err is OOB and s[-1:] == '"':
            s = s[:-1]
        elif err is OOB and s[-1:] == ':':
            s = s + '""'
        elif err is EXPECTING_COLON:
            s = s + ':""'
        elif find_open_bracket(s):
            c = find_open_bracket(s)
            if c:
                s = s + c
        elif err is EXPECTING_OBJECT:
            if s[-1:] == ',':
                s = s[:-1]
            else:
                s = s + '}'
        elif err is EXPECTING_COMMA and last_error is EXPECTING_COMMA:
            s = s + '}'
        elif err is EXPECTING_COMMA and last_error is EXPECTING_PROPERTY:
            s = s + '}'
        elif err is EXPECTING_COMMA and last_error is UNTERMINATED:
            s = s + '}'
        elif err is EXPECTING_COMMA:
            s = s + ','
        elif err is EXPECTING_VALUE:
            s = s + ""
        elif err == NO_JSON:
            s = s[:-1]
        else:
            raise Exception("Failed to parse string '{}': {}".format(
                s, e.args[0]))
        return parse_truncated_json(s, depth, last_error=err)
    return o


def find_open_bracket(s):
    lsb = s.rfind('[')
    rsb = s.rfind(']')
    if lsb > -1 and (rsb == -1 or lsb > rsb):
        sb_append = ']'
    else:
        sb_append = None

    lbr = s.rfind('{')
    rbr = s.rfind('}')
    if lbr > -1 and (rbr == -1 or lbr > rbr):
        br_append = '}'
    else:
        br_append = None

    if sb_append and not br_append:
        return sb_append
    elif br_append and not sb_append:
        return br_append
    elif lbr > lsb:
        return br_append
    else:
        return sb_append


def parse_error(msg):
    c = int(re.findall(r'\(char (\d+)\)', str(msg))[0])

    if UNTERMINATED in msg:
        return UNTERMINATED, c
    if EXPECTING_OBJECT in msg:
        return EXPECTING_OBJECT, c
    if EXPECTING_COLON in msg:
        return EXPECTING_COLON, c
    if EXPECTING_PROPERTY in msg:
        return EXPECTING_PROPERTY, c
    if OOB in msg:
        return OOB, c
    if EXPECTING_COMMA in msg:
        return EXPECTING_COMMA, c
    if NO_JSON in msg:
        return NO_JSON, c
    if EXPECTING_VALUE in msg:
        return EXPECTING_VALUE, c
    return None, c


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

    return s[x:y]


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def find_level(s):
    x = find_nth(s, '[', 2) + 1
    try:
        y = s.index(']', x)
    except ValueError:
        return None
    return s[x:y]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--log-level')
    p.add_argument('out_file')
    args = p.parse_args()
    _l = args.log_level or 'info'
    level = getattr(logging, _l.upper())
    log.setLevel(level)

    f = open(args.out_file, 'w')

    failed = 0
    succeeded = 0
    for line in sys.stdin.readlines():
        log.debug('-'*100)
        log.debug(line)
        out = {}
        out['took'] = find_field(line, name='took')
        out['level'] = find_level(line)
        log.debug(out)

        source = find_field(line, name='source')
        if not all((source, out['took'])):
            log.info("Skipping message '{}'".format(line))
            continue

        source = source.replace('\\"', '\"')
        try:
            o = parse_truncated_json(source)
        except Exception as e:
            failed += 1
            log.warning("Failed to parse line; Error: {}; line: {}".format(
                e.args[0], line))
            print(line)
            continue
        out['source'] = o
        succeeded += 1

        f.write(json.dumps(out))
        log.info(out)
    f.close()

    log.info("S: {}; F: {}".format(succeeded, failed))

