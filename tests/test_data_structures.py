import os
from unittest import mock

import pytest

from pytest_testdox import formatters
from pytest_testdox.data_structures import Node, PatternConfig, Result


@pytest.fixture
def node():
    return Node(title='title', class_name='class_name', module_name='module')


@pytest.fixture
def report():
    return mock.Mock(
        spec=('nodeid', 'outcome'),
        nodeid='folder/test_file.py::test_title',
        outcome='passed',
    )


@pytest.fixture
def pattern_config():
    return PatternConfig(
        files=['test_*.py'], functions=['test*'], classes=['Test*']
    )


class TestNode:
    def test_parse_should_return_a_node_instance(self, pattern_config):
        nodeid = 'tests/test_module.py::test_title'
        node = Node.parse(nodeid, pattern_config)

        assert isinstance(node, Node)

    def test_parse_should_parse_node_id_attributes(self, pattern_config):
        nodeid = 'tests/test_module.py::test_title'
        node = Node.parse(nodeid, pattern_config)

        assert node.title == formatters.format_title(
            'test_title', pattern_config.functions
        )
        assert node.module_name == (
            formatters.format_module_name(
                'tests/test_module.py', pattern_config.files
            )
        )

    @pytest.mark.parametrize(
        ('attribute,value'),
        (
            ('title', ' new title '),
            ('class_name', ' new class name '),
        ),
    )
    def test_parse_should_use_overridden_attribute_instead_of_parse_node_id(
        self, attribute, value, pattern_config
    ):
        nodeid = 'tests/test_module.py::test_title'

        node = Node.parse(nodeid, pattern_config, **{attribute: value})

        result = getattr(node, attribute)

        assert result == formatters.trim_multi_line_text(value)

    @pytest.mark.parametrize(
        'nodeid,class_name',
        (
            ('tests/test_module.py::test_title', None),
            (
                'tests/test_module.py::TestClassName::()::test_title',
                formatters.format_class_name('TestClassName', ['Test*']),
            ),
            (
                'tests/test_module.py::TestClassName::test_title',
                formatters.format_class_name('TestClassName', ['Test*']),
            ),
        ),
    )
    def test_parse_with_class_name(self, pattern_config, nodeid, class_name):
        node = Node.parse(nodeid, pattern_config)

        assert node.class_name == class_name


class TestResult:
    @pytest.fixture
    def result(self, node):
        return Result('passed', node)

    def test_create_should_return_a_result_with_a_parsed_node(
        self, report, pattern_config
    ):
        result = Result.create(report, pattern_config)

        assert isinstance(result, Result)
        assert result.outcome == report.outcome
        assert result.node == Node.parse(report.nodeid, pattern_config)

    @pytest.mark.parametrize(
        'report_attribute,parameter,value',
        (
            ('testdox_title', 'title', 'some title'),
            ('testdox_class_name', 'class_name', 'some class name'),
        ),
    )
    def test_create_should_call_parse_with_overridden_attributes(
        self, report_attribute, parameter, value, report, pattern_config
    ):
        setattr(report, report_attribute, value)

        result = Result.create(report, pattern_config)

        kwargs = {parameter: value}

        assert result.node == Node.parse(
            nodeid=report.nodeid, pattern_config=pattern_config, **kwargs
        )

    def test_str_should_format_result_str(self, node):
        node.title = 'some{}text'.format(os.linesep)
        result = Result('passed', node)

        assert formatters.format_result_str(' [x] ', node.title) in str(result)
