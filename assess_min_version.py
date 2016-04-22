#!/usr/bin/env python
from __future__ import print_function

import argparse
import logging
import subprocess
import sys

from deploy_stack import BootstrapManager
from utility import (
    add_basic_testing_arguments,
    configure_logging,
    make_charm,
    temp_dir,
)


__metaclass__ = type


log = logging.getLogger("assess_version")


class JujuAssertionError(AssertionError):
    """Exception for juju assertion failures."""


def assert_fail(client, charm, ver, cur, name):
    try:
        client.deploy(charm, service=name)
    except subprocess.CalledProcessError:
        return
    raise JujuAssertionError(
        'assert_fail failed min: {} cur: {}'.format(ver, cur))


def assert_pass(client, charm, ver, cur, name):
    try:
        client.deploy(charm, service=name)
        client.wait_for_started()
    except subprocess.CalledProcessError:
        raise JujuAssertionError(
            'assert_pass failed min: {} cur: {}'.format(ver, cur))


def get_current_version(client, juju_path):
    current = client.get_version(juju_path=juju_path).split('-')[:-2]
    return '-'.join(current)


def assess_deploy(client, assertion, ver, current, name):
    with temp_dir() as charm_dir:
        log.info("Testing min version {}".format(ver))
        make_charm(charm_dir, ver)
        assertion(client, charm_dir, ver, current, name)


def assess_min_version(client, args):
    current = get_current_version(client, args.juju_bin)
    tests = [['1.25.0', 'name1250', assert_pass],
             ['99.9.9', 'name9999', assert_fail],
             ['99.9-alpha1', 'name999alpha1', assert_fail],
             ['1.2-beta1', 'name12beta1', assert_pass],
             ['1.25.5.1', 'name12551', assert_pass],
             ['2.0-alpha1', 'name20alpha1', assert_pass],
             [current, 'current', assert_pass]]
    for ver, name, assertion in tests:
        assess_deploy(client, assertion, ver, current, name)


def parse_args(argv):
    """Parse all arguments."""
    parser = argparse.ArgumentParser(description="Juju min version")
    add_basic_testing_arguments(parser)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    configure_logging(args.verbose)
    bs_manager = BootstrapManager.from_args(args)
    with bs_manager.booted_context(args.upload_tools):
        assess_min_version(bs_manager.client, args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
