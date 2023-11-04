#!/usr/bin/env python3

import sys
import json
import os
from os.path import join

from collections import namedtuple

from lxml import etree
from lxml.etree import _Element as Element
from lxml.etree import tostring

ParamType = namedtuple(
	"ParamType", [
		"type",
		"comment",
		"pattern",
	],
	defaults=(
		"",  # type
		"",  # comment
		"",  # pattern
	),
)


# %Y-%m-%d %H:%M:%S or %Y-%m-%d %H:%M
datetimePattern = "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}(:[0-9]{2})?$"


paramTypeMapping = {
	"any": ParamType(),

	"str": ParamType("string"),
	"srt": ParamType("string"),

	"str_int": ParamType("string", pattern="^[0-9]+$"),

	"int": ParamType("number"),
	"float": ParamType("number"),
	"str_float": ParamType("str", "float as string"),

	"datetime": ParamType("string", "datetime", pattern=datetimePattern),
	"datetime, float": ParamType(("string", "number"), "datetime or number"),
	"datetime, null": ParamType(("string", "null"), "datetime or null", pattern=datetimePattern),

	"bool": ParamType("boolean"),
	"true_if_exists": ParamType("boolean", "true if exists"),

	"list": ParamType("array"),
	"list, str": ParamType(("array", "string")),

	"dict": ParamType("object"),

	"null": ParamType("null"),
	
	"int, null": ParamType(("number", "null"), "int or null"),
	"dynamic": ParamType("", "dynamic type"),

	"list, str": ParamType(("array", "string")),
	"list, int": ParamType(("array", "number"), "array or int"),
	"int, list": ParamType(("number", "array"), "int or array"),
	"str, list": ParamType(("string", "array"), "string or array"),
}


def toStr(elem):
	return tostring(
		elem,
		method="html",
		pretty_print=True,
	).decode("utf-8")


def dataToPrettyJson(data):
	return json.dumps(
		data,
		sort_keys=False,
		indent=2,
		ensure_ascii=True,
	)



def getChoiceJsonParam(param: "Element") -> dict:
	paramName = param.attrib.get("name")
	description = param.attrib.get("comment")
	values = []
	comments = {}
	default = None
	valueTypes = set()
	for choiceElem in param.getchildren():
		if choiceElem.tag != "choice":
			# print(f"getChoiceJsonParam: expected choice tag, got {toStr(choiceElem)}")
			return
		value = choiceElem.attrib.get("value")
		if value is None:
			print(f"choice with no value: {toStr(choiceElem)}")
			return
		_type = choiceElem.attrib.get("type")
		if _type:
			valueTypes.add(_type)
			if _type == "int":
				value = int(value)
			elif _type == "str":
				pass
			else:
				print(f"invalid choice value in {toStr(choiceElem)}")
		values.append(value)
		comment = choiceElem.attrib.get("comment")
		if comment:
			comments[value] = comment
		if choiceElem.attrib.get("default"):
			default = value
	seqauential = False
	if not values:
		print(f"choice with no values: {toStr(param)}")
	elif len(valueTypes) > 1:
		print(f"more than one value type for: {toStr(param)}")
	elif valueTypes:
		_type = list(valueTypes)[0]
		if _type == "int":
			values = sorted(values)
			if values[-1] - values[0] == len(values) - 1:
				# print(f"seqauential: {values}")
				seqauential = True
			else:
				print(f"non-seqauential integer choice values: {values}")

	paramJson = {}
	if paramName:
		paramJson["name"] = paramName
	if description is not None:
		paramJson["description"] = description
	if seqauential:
		paramJson["schema"] = {
			"type": "number",
			"minimum": values[0],
			"maximum": values[-1],
		}
	else:
		paramJson["schema"] = {
			"enum": values,
		}
	if default is not None:
		if default in ("true", "false"):
			default = default == "true"
		else:
			try:
				default = int(default)
			except ValueError:
				pass
		paramJson["default"] = default
	if comments:
		paramJson["schema"]["__value_comment__"] = comments
	return paramJson


def getListItemSchema(item: "Element") -> "dict | list":
	# possible keys for itemSchema: title, type, required: list[str], properties: dict
	_type = item.attrib.get("type")
	if not _type:
		print(f"item has no type: {toStr(item)}")
		return
	if _type == "choice":
		itemJson = {
			"title": item.attrib.get("comment", ""),
		}
		_tmpItem = getChoiceJsonParam(item)
		if _tmpItem is None:
			return
		itemJson.update(_tmpItem)
		if "description" in itemJson:
			del itemJson["description"]
		return itemJson
	if _type == "dict":
		res = {
			"title": item.attrib.get("comment", ""),
			"type": "object",
		}
		setDictParamsSchema(item, res)
		return res

	newType = paramTypeMapping[_type]

	return {
		"title": item.attrib.get("comment", ""),
		"type": newType.type,
	}


def getMultiTypeListItemSchema(items: "list[Element]") -> "dict | list":
	result = []
	for index, item in enumerate(items):
		schema = {"index": index}
		schema2 = getListItemSchema(item)
		if schema2 is None:
			continue
		schema.update(schema2)
		result.append(schema)
	return result


def getListSchema(elem: "Element", newType="array") -> "dict | list":
	schema = {
		"type": newType,
	}
	items = elem.findall("item")
	if items:
		if len(items) > 1:
			# print(f"multi-type array: {toStr(elem)}")
			itemSchema = getMultiTypeListItemSchema(items)
		else:
			itemSchema = getListItemSchema(items[0])
		if itemSchema:
			schema["items"] = itemSchema

	length = elem.attrib.get("length")
	if length and length != "-1":
		schema["length"] = length
	return schema


def setDynamicKeys(param: "Element", schema: dict):
	schema["dynamic_keys"] = True
	key = param.find("key")
	if key is None:
		return
	value = param.find("value")
	if value is None:
		print(f"<key> without <value>: {toStr(param)}")
		return
	schema["__key__"] = {
		"type": key.attrib.get("type", ""),
		"title": key.attrib.get("comment", ""),
	}
	valueJson = getJsonParam(value)
	if "schema" in valueJson:
		valueJson.update(valueJson.pop("schema"))
	schema["__value__"] = valueJson


def setDictParamsSchema(param: "Element", schema: dict):
	properties = {}
	for subParam in getParams(param):
		name = subParam.pop("name")
		title = ""
		if "description" in subParam:
			title = subParam.pop("description")
		prop = {
			"title": title,
		}
		if "schema" in subParam:
			prop.update(subParam.pop("schema"))
		prop.update(subParam)
		properties[name] = prop

	if param.attrib.get("dynamic_keys") == "true":
		setDynamicKeys(param, schema)
	elif param.find("key") is not None:
		print(f"forgot dynamic_keys=true: {toStr(param)}")

	schema["properties"] = properties



def addParamExtraAttrs(param: "Element", paramJson: dict):
	default = param.attrib.get("default")
	if default is not None:
		paramJson["required"] = False
		paramJson["default"] = default
	elif param.attrib.get("optional"):
		paramJson["required"] = False



def getJsonParam(param: "Element") -> dict:
	paramName = param.attrib.get("name")

	paramType = param.attrib.get("type")
	if not paramType:
		print(f"{branch=}: param type is empty: {toStr(param)}")
		#return

	if paramType == "choice":
		return getChoiceJsonParam(param)

	description = param.attrib.get("comment", "")

	paramValue = param.attrib.get("value")

	if paramType:
		newType = paramTypeMapping[paramType]
	else:
		newType = ParamType()

	if paramValue in ("true", "false"):
		if description:
			description += ", "
		description += f"always {paramValue}"
	elif paramValue:
		# like a choice with one value
		paramJson = {
			"name": paramName,
			"description": description,
			"schema": {
				"enum": [paramValue],
			#	"type": newType.type,
			},
		}
		addParamExtraAttrs(param, paramJson)
		return paramJson

	if newType.comment:
		description = newType.comment + ", " + description

	if "array" in newType.type:
		schema = getListSchema(param, newType.type)
	else:
		schema = {
			"type": newType.type,
		}		

	if newType.pattern:
		schema["pattern"] = newType.pattern
	elif paramType == "dict":
		setDictParamsSchema(param, schema)
	else:
		pattern = param.attrib.get("pattern")
		if pattern:
			schema["pattern"] = pattern
	paramJson = {}
	if paramName:
		paramJson["name"] = paramName
	paramJson.update({
		"description": description,
		"schema": schema,
	})
	addParamExtraAttrs(param, paramJson)
	return paramJson


def getParams(elem) -> "list":
	params = []
	for param in elem.getchildren():
		if param.tag != "param":
			continue
		if not param.attrib.get("name"):
			print(f"{branch=}: param name is empty: {toStr(param)}")
			continue
		jsonParam = getJsonParam(param)
		if jsonParam is None:
			continue
		params.append(jsonParam)
	return params


def getJsonMethod(handlerName: str, method: "Element", authTypes: list[str]):
	if method.tag != "method":
		# print(f"expected method element, got {method.tag}: {method}")
		return
	methodName = method.attrib.get("name")
	if not methodName:
		print(f"method has no name: {toStr(method)}")
		return
	inputElem = method.find("input")
	if inputElem is None:
		print(f"no <input> for: {toStr(method)}")
		return
	outputElem = method.find("output")
	if outputElem is None:
		print(f"{branch=}, no <output> for: {toStr(method)}")
		return

	params = getParams(inputElem)

	methodDesc = method.attrib.get("comment", "")
	outputComment = outputElem.attrib.get("comment", "")
	outputType = outputElem.attrib.get("type")
	outputValue = outputElem.attrib.get("value")

	resultName = ""

	resultValues: "list | None" = None
	if outputValue in ("true", "false"):
		#if outputComment:
		#	outputComment += ", "
		#outputComment += f"always {outputValue}"
		resultName = f"Response (always {outputValue})"
	elif outputValue:
		resultValues = [outputValue]


	jsonMethod = {
		"name": handlerName + "." + methodName,
		"description": methodDesc,
		"auth_type": authTypes,
	}
	requires_perm = method.attrib.get("requires_perm")
	if requires_perm:
		jsonMethod["requires_perm"] = [
			x.strip()
			for x in requires_perm.split(",")
		]
	jsonMethod["params"] = params

	resultType = ParamType()


	if not (outputValue or outputType):
		print(f"no output type nor value: {branch=}: {toStr(method)}")
		return None
	if outputType == "choice":
		resultValues = []
		for param in outputElem.getchildren():
			if param.tag != "choice":
				print(f"getJsonMethod: expected choice tag, got: {toStr(param)}")
				continue
			value = param.attrib.get("value")
			if not value:
				print("empty value in {toStr(param)}")
				continue
			resultValues.append(value)
	elif outputType:
		resultType = paramTypeMapping[outputType]
	resultParams = {}
	for param in outputElem.getchildren():
		if param.tag != "param":
			continue
		paramName = param.attrib.get("name")
		if not paramName:
			print(f"{branch=}: param name is empty: {toStr(param)}")
			continue
		jsonParamTmp = getJsonParam(param)
		if jsonParamTmp is None:
			continue
		del jsonParamTmp["name"]
		title = ""
		if "description" in jsonParamTmp:
			title = jsonParamTmp.pop("description")
		jsonParam = {"title": title}
		if "schema" in jsonParamTmp:
			jsonParam.update(jsonParamTmp.pop("schema"))
		jsonParam.update(jsonParamTmp)
		resultParams[paramName] = jsonParam
	if not resultName:
		if resultValues is not None:
			resultName = "Response (one of following values)"
		elif resultType.type:
			resultName = f"Response ({resultType.type})"
	result = {
		"name": resultName,
		"summary": outputComment,
	}
	if resultType.type or resultValues:
		resultSchemaType = resultType.type
		if not resultSchemaType:
			pass # FIXME: str or int?
		resultSchema = {
			"title": "",
			"type": resultSchemaType,
		}
		if resultParams:
			resultSchema["properties"] = resultParams
		result["schema"] = resultSchema
		if resultValues:
			resultSchema["enum"] = resultValues

	jsonMethod["result"] = result
	# jsonMethod["errors"] = []
	return jsonMethod


def convertSubsystem(handler, branch, outDir):
	handlerName = handler.attrib.get("name")
	if not handlerName:
		print("handler has no name")
		return

	branchDir = join(outDir, branch)
	os.makedirs(branchDir, exist_ok=True)

	methods = []
	for method in handler.getchildren():
		if method.tag != "method":
			continue
		authTypesStr = method.attrib.get("auth_type")
		if authTypesStr is None:
			print(f"no auth_type: {branch=}: {toStr(method)}")
			return
		if authTypesStr:
			authTypes = [x.strip() for x in authTypesStr.split(",")]
			for authType in authTypes:
				if authType not in ("ADMIN", "NORMAL_USER", "VOIP_USER", "ANONYMOUS"):
					print(f"bad auth_type={authType} in {authTypesStr!r}")
		else:
			authTypes = ["ADMIN", "NORMAL_USER", "VOIP_USER"]
		jsonMethod = getJsonMethod(handlerName, method, authTypes)
		if jsonMethod is None:
			continue

		methods.append(jsonMethod)

	with open(join(branchDir, handlerName + ".json"), "w") as _file:
		_file.write(dataToPrettyJson({
			"openrpc": "1.2.1",
			"info": {
				"title": f"IBSng: branch {branch}: {handlerName}",
				"version": "1.0.0",
			},
			"methods": methods,
		}))


def convert(xmlFileName, branch, outDir):
	with open(xmlFileName, encoding="utf-8") as _file:
		doc = etree.XML(_file.read().encode("utf-8"))

	for handler in doc.getchildren():
		if handler.tag != "handler":
			continue
		convertSubsystem(handler, branch, outDir)


if __name__ == '__main__':
	fpath = sys.argv[1]
	branch = sys.argv[2]
	outDir = sys.argv[3]
	convert(fpath, branch, outDir)

