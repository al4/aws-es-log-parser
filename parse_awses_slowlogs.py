import argparse
import json
import sys
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

UNTERMINATED = "Unterminated string"
EXPECTING_OBJECT = "Expecting object"
EXPECTING_COLON = "Expecting : delimiter"
EXPECTING_PROPERTY = "Expecting property name:"
OOB = "end is out of bounds"
EXPECTING_COMMA = "Expecting , delimiter"
NO_JSON = "No JSON object could be decoded"


def parse_truncated_json(s, depth=0, last_error=None):
    log.debug(s)
    if depth > 10:
        raise Exception("Too deep for string {}, last error: {}".format(
            s, last_error))
    try:
        o = json.loads(s)
    except ValueError as e:
        log.debug('string {} gives {}'.format(s, e.args[0]))
        err = parse_error(e.args[0])
        log.debug('err {}: {} (last: {})'.format(err, e.args[0], last_error))

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
        elif err is EXPECTING_COMMA and last_error is EXPECTING_COMMA:
            s = s[:-5]
        elif err is EXPECTING_COMMA:
            s = s + ','
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


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--log-level')
    args = p.parse_args() 
    _l = args.log_level or 'info'
    level = getattr(logging, _l.upper())
    log.setLevel(level)

    failed = 0
    succeeded = 0
    for line in sys.stdin.readlines():
        out = {}
        source = find_field(line, name='source')
        log.debug("Source: {}".format(source))
        took = find_field(line, name='took')
        out['took'] = took
        log.debug("Took: {}".format(took))

        if not all((source, took)):
            log.info("Skipping message '{}'".format(line))
            continue

        source = source.replace('\\"', '\"')
        try:
            o = parse_truncated_json(source)
        except Exception as e:
            failed += 1
            log.warn("Failed to parse line; Error: {}; line: {}".format(
                e.args[0], line))
            continue
        out['source'] = o
        succeeded += 1
        log.info(out)

    log.info("S: {}; F: {}".format(succeeded, failed))
    # {"journald_message":"23:34:12.641Z\\",\\"cardUid\\":\\"ed5e704a-eed5-406f-b307-e7782ac54951\\",\\"billingA"}
