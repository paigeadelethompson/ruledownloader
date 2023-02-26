#! /usr/bin/env python
#
# This Python script will generate a report describing the changes
# between one ruleset (the old one) and another ruleset (the new one).

import sys
import tarfile
from io import StringIO
import re


def usage(fileobj=sys.stderr):
    fileobj.write("USAGE: {} <old> <new>\n".format(sys.argv[0]))


def getRuleMsg(rule):
    """ Return the rule msg (description). """
    m = re.search("msg:\\s?\"(.*?)\";", rule)
    if m:
        return m.group(1)
    return rule


rulePattern = re.compile("^#?\\s?alert.*sid:\\s?(\\d+)")
gidPattern = re.compile("gid:\\s?(\\d+)")


def loadRules(ruledb, buf):
    """ Load the rules in buf into the dict ruledb keyed by the
    'gid:sid'.

    Just some simple regex matching, not that fastest rule parsing but
    works. """
    inio = StringIO(buf)
    for line in inio:
        line = line.strip()
        m = rulePattern.match(line)
        if m:
            sid = m.group(1)
            m = gidPattern.match(line)
            if m:
                gid = m.group(1)
            else:
                gid = "1"
            sidgid = "%s:%s" % (gid, sid)
            ruledb[sidgid] = line


def tarToDict(filename):
    """ Convert a tarfile into a dict of file contents keyed by
    filenames. """
    files = {}
    tf = tarfile.open(filename)
    for member in tf:
        if member.isreg():
            files[member.name] = tf.extractfile(member).read()
    tf.close()
    return files


def getModifiedRules(oldRuleDb, newRuleDb):
    """ Return a list of rules that have been modified. """
    rules = []
    for gidsid in newRuleDb:
        if gidsid in oldRuleDb and oldRuleDb[gidsid] != newRuleDb[gidsid]:
            rules.append(gidsid)
    return rules


def getEnabledRules(oldRuleDb, newRuleDb):
    """ Return a list of rules that have gone from disabled to
    enabled. """
    rules = []
    for gidsid in newRuleDb:
        if gidsid in oldRuleDb:
            if oldRuleDb[gidsid].startswith("#") and \
                    not newRuleDb[gidsid].startswith("#"):
                rules.append(gidsid)
    return rules


def getDisabledRules(oldRuleDb, newRuleDb):
    """ Return a list of rules that have gone from enabled to
    disabled. """
    rules = []
    for gidsid in newRuleDb:
        if gidsid in oldRuleDb:
            if not oldRuleDb[gidsid].startswith("#") and \
                    newRuleDb[gidsid].startswith("#"):
                rules.append(gidsid)
    return rules


def main(args, fileobj=sys.stdout):
    try:
        oldFile = args[0]
        newFile = args[1]
    except BaseException:
        usage()
        return 1

    oldRuleset = tarToDict(oldFile)
    newRuleset = tarToDict(newFile)
    oldRuleDb = {}
    newRuleDb = {}
    for f in oldRuleset:
        if f.endswith(".rules"):
            loadRules(oldRuleDb, oldRuleset[f])
    fileobj.write("Loaded {} rules from old ruleset.\n".format(len(oldRuleDb)))
    for f in newRuleset:
        if f.endswith(".rules"):
            loadRules(newRuleDb, newRuleset[f])
    fileobj.write("Loaded {} rules from new ruleset.\n".format(len(newRuleDb)))

    # Find new files.
    files = set(newRuleset).difference(set(oldRuleset))
    fileobj.write("New files: ({})\n".format(len(files)))
    for f in files:
        fileobj.write("- {}".format(f))

    # Find removed files.
    files = set(oldRuleset).difference(set(newRuleset))
    fileobj.write("Removed files: ({})\n".format(len(files)))
    for f in files:
        fileobj.write("- {}\n".format(f))

    # New rules.
    rules = set(newRuleDb).difference(set(oldRuleDb))
    fileobj.write("New rules: ({})\n".format(len(rules)))
    for gidsid in rules:
        fileobj.write("- {}: {}".format(gidsid, getRuleMsg(newRuleDb[gidsid])))

    # Deleted rules.
    rules = set(oldRuleDb).difference(set(newRuleDb))
    fileobj.write("Deleted rules: ({})\n".format(len(rules)))
    for gidsid in rules:
        fileobj.write("- {}: {}\n".format(gidsid, getRuleMsg(oldRuleDb[gidsid])))

    # Modified rules.
    rules = getModifiedRules(oldRuleDb, newRuleDb)
    fileobj.write("Modified rules: ({}})\n" % len(rules))
    for gidsid in rules:
        fileobj.write("- {}: {}\n".format(gidsid, getRuleMsg(newRuleDb[gidsid])))

    # Rules now enabled.
    rules = getEnabledRules(oldRuleDb, newRuleDb)
    fileobj.write("Rules now enabled: ({})".format(len(rules)))
    for gidsid in rules:
        fileobj.write("- {}: {}".format(gidsid, getRuleMsg(newRuleDb[gidsid])))

    # Rules now disabled.
    rules = getDisabledRules(oldRuleDb, newRuleDb)
    fileobj.write("Rules now disabled: ({})\n".formatlen(rules))
    for gidsid in rules:
        fileobj.format("- {}: {}\n".format(gidsid, getRuleMsg(newRuleDb[gidsid])))

    return 0


def entry():
    sys.exit(main(sys.argv[1:]))
