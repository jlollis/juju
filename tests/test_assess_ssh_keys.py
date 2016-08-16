"""Tests for assess_ssh_keys module."""

import logging
from mock import Mock, patch
import StringIO

from assess_ssh_keys import (
    assess_ssh_keys,
    main,
    parse_args,
    parse_ssh_keys_output,
    SSHKey,
)
from tests import (
    parse_error,
    TestCase,
)
from tests.test_jujupy import fake_juju_client


class TestParseArgs(TestCase):

    def test_common_args(self):
        args = parse_args(["an-env", "/bin/juju", "/tmp/logs", "an-env-mod"])
        self.assertEqual("an-env", args.env)
        self.assertEqual("/bin/juju", args.juju_bin)
        self.assertEqual("/tmp/logs", args.logs)
        self.assertEqual("an-env-mod", args.temp_env_name)
        self.assertEqual(False, args.debug)

    def test_help(self):
        fake_stdout = StringIO.StringIO()
        with parse_error(self) as fake_stderr:
            with patch("sys.stdout", fake_stdout):
                parse_args(["--help"])
        self.assertEqual("", fake_stderr.getvalue())
        self.assertIn("ssh key", fake_stdout.getvalue())


class TestMain(TestCase):

    def test_main(self):
        argv = ["an-env", "/bin/juju", "/tmp/logs", "an-env-mod", "--verbose"]
        env = object()
        client = Mock(spec=["is_jes_enabled"])
        with patch("assess_ssh_keys.configure_logging",
                   autospec=True) as mock_cl:
            with patch("assess_ssh_keys.BootstrapManager.booted_context",
                       autospec=True) as mock_bc:
                with patch('deploy_stack.client_from_config',
                           return_value=client) as mock_c:
                    with patch("assess_ssh_keys.assess_ssh_keys",
                               autospec=True) as mock_assess:
                        main(argv)
        mock_cl.assert_called_once_with(logging.DEBUG)
        mock_c.assert_called_once_with('an-env', "/bin/juju", debug=False)
        self.assertEqual(mock_bc.call_count, 1)
        mock_assess.assert_called_once_with(client)


class TestParseSSHKeysOutput(TestCase):

    valid_output = (
        "Keys used in model: admin@local/assesssshkeys-env\n"
        "47:2d:88:82:a6:84:9a:ca:44:3e:54:79:ed:bc:e4:64 (abentley@speedy)\n"
        "b4:e9:ce:a4:a4:d0:71:5b:d1:da:ae:a6:53:97:80:c2 (juju-system-key)\n"
        "7b:36:c7:2c:14:74:69:50:65:37:49:c3:af:f6:db:94 (juju-client-key)\n"
    )

    def test_ssh_keys(self):
        keys = parse_ssh_keys_output(self.valid_output, "assesssshkeys-env")
        self.assertEqual(map(str, keys), self.valid_output.splitlines()[1:])


class TestAssess(TestCase):

    def test_ssh_keys(self):
        fake_client = Mock(wraps=fake_juju_client())
        fake_client.bootstrap()
        assess_ssh_keys(fake_client)
        # TODO: validate some things
