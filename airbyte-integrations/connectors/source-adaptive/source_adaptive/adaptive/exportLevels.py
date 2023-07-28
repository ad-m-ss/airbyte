from jinja2 import Template

from collections.abc import MutableMapping

from datetime import datetime
from typing import Generator

from airbyte_cdk.models import (
    AirbyteMessage,
    AirbyteRecordMessage,
    Type,
)
from source_adaptive.adaptive.base import Adaptive
from airbyte_cdk.sources import Source
from datetime import datetime


class AdaptiveExportLevels(Adaptive):
    def construct_payload(self) -> Generator[str, None, None]:
        yield self.construct_payload_fast()

    def construct_payload_fast(self) -> str:
        """
        Generate the xml that is sent to the request using jinja templating
        """

        TEMPLATE = """<?xml version='1.0' encoding='UTF-8'?>
        <call method="{{method_obj["method"]}}" callerName="Airbyte - auto">
            <include versionName="{{method_obj["version"]}}" inaccessibleValues="true"/>
            <credentials login="{{username}}" password="{{password}}"/>
        </call>"""

        payload = Template(TEMPLATE).render(**self.config)
        return payload

    def generate_table_name(self):
        return "exportLevels" + "_" + self.config["method_obj"]["version"]

    def generate_table_schema(self):
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "currency": {"type": "string"},
                "shortName": {"type": "string"},
                "isElimination": {"type": "string"},
                "isLinked": {"type": "string"},
                "workflowStatus": {"type": "string"},
                "isImportable": {"type": "string"},
                "attributes": {"type": "string"},
                "availableStart": {"type": "string"},
                "availableEnd": {"type": "string"},
                "hasChildren": {"type": "string"},
                "parent_id": {"type": "string"},
                "version": {"type": "string"},
            },
        }

        return json_schema

    def parse_attributes(self, d) -> str:
        if not d:
            return ""

        attribute_records = []

        attributes = d.get("attribute")
        if isinstance(attributes, list):
            for attribute in attributes:
                record = {}
                for k, v in attribute.items():
                    record[k.replace("@", "")] = v

                attribute_records.append(record)
        elif isinstance(attributes, dict):
            record = {}
            for k, v in attributes.items():
                record[k.replace("@", "")] = v
            attribute_records.append(record)

        return str(attribute_records)

    def parse_level(self, d: MutableMapping, parent_id) -> Generator[AirbyteMessage, None, None]:

        version = self.config["method_obj"]["version"]

        if isinstance(d, list):
            for i in d:
                yield from self.parse_level(i, parent_id)
        else:
            dict_keys = list(d.keys())
            if "level" in dict_keys:
                yield from self.parse_level(d["level"], d.get("@id"))

                lvl = {
                    "id": d.get("@id"),
                    "name": d.get("@name"),
                    "currency": d.get("@currency"),
                    "shortName": d.get("@shortName"),
                    "isElimination": d.get("@isElimination"),
                    "isLinked": d.get("@isLinked"),
                    "workflowStatus": d.get("@workflowStatus"),
                    "isImportable": d.get("@isImportable"),
                    "availableStart": d.get("@availableStart"),
                    "availableEnd": d.get("@availableEnd"),
                    "hasChildren": d.get("@hasChildren"),
                    "attributes": self.parse_attributes(d.get("attributes", "")),
                    "parent_id": parent_id,
                    "version": version,
                }
                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(
                        stream=self.generate_table_name(), data=lvl, emitted_at=int(datetime.now().timestamp()) * 1000
                    ),
                )
            else:
                lvl = {
                    "id": d.get("@id"),
                    "name": d.get("@name"),
                    "currency": d.get("@currency"),
                    "shortName": d.get("@shortName"),
                    "isElimination": d.get("@isElimination"),
                    "isLinked": d.get("@isLinked"),
                    "workflowStatus": d.get("@workflowStatus"),
                    "isImportable": d.get("@isImportable"),
                    "availableStart": d.get("@availableStart"),
                    "availableEnd": d.get("@availableEnd"),
                    "hasChildren": d.get("@hasChildren"),
                    "attributes": self.parse_attributes(d.get("attributes", "")),
                    "parent_id": parent_id,
                    "version": version,
                }

                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(
                        stream=self.generate_table_name(), data=lvl, emitted_at=int(datetime.now().timestamp()) * 1000
                    ),
                )

    def generate_table_row(self) -> Generator[AirbyteMessage, None, None]:

        for response in self.perform_request():
            response_data = self.get_data_from_response(response)

            data = response_data["levels"]["level"]

            yield from self.parse_level(data, "")
