#!/usr/bin/env python3

import sys
import json
import os
from os.path import join

from lxml import etree
from lxml.etree import _Element as Element
from lxml.etree import tostring

paramTypeMapping = {
	"any": ("", ""),

	"str": ("string", ""),
	"srt": ("string", ""),

	"str_int": ("string", ""),

	"int": ("number", ""),
	"float": ("number", ""),
	"str_float": ("str", "float as string"),

	"datetime": ("string", "datetime"),
	"datetime, float": (("string", "number"), "datetime or number"),
	"datetime, null": (("string", "null"), "datetime or null"),

	"bool": ("boolean", ""),
	"true_if_exists": ("boolean", "true if exists"),

	"list": ("array", ""),
	"list, str": (("array", "string"), ""),

	"dict": ("object", ""),

	"null": ("null", ""),
	
	"int, null": (("number", "null"), "int or null"),
	"dynamic": ("", "dynamic type"),

	"list, str": (("array", "string"), ""),
	"list, int": (("array", "number"), "array or int"),
	"int, list": (("number", "array"), "array or int"),
	"str, list": (("string", "array"), "array or string"),
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
	for choiceElem in param.getchildren():
		if choiceElem.tag != "choice":
			# print(f"getChoiceJsonParam: expected choice tag, got {toStr(choiceElem)}")
			return
		value = choiceElem.attrib.get("value")
		if value is None:
			print(f"choice with no value: {toStr(choiceElem)}")
			return
		values.append(value)
		comment = choiceElem.attrib.get("comment")
		if comment:
			comments[value] = comment
	if not values:
		print(f"choice with no values: {toStr(param)}")
	paramJson = {}
	if paramName:
		paramJson["name"] = paramName
	if description is not None:
		paramJson["description"] = description
	paramJson["enum"] = values
	if comments:
		paramJson["value_comment"] = comments
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
		params = getParams(item)
		for param in params:
			if "schema" in param:
				param.update(param.pop("schema"))
		return {
			"title": item.attrib.get("comment", ""),
			"type": "object",
			"params": params,
		}

	return {
		"title": item.attrib.get("comment", ""),
		"type": _type,
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


def getListSchema(elem: "Element", newParamType="array") -> "dict | list":
	schema = {
		"type": newParamType,
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
		newParamType, typeComment = paramTypeMapping[paramType]
	else:
		newParamType, typeComment = "", ""

	if paramValue:
		# like a choice with one value
		paramJson = {
			"name": paramName,
			"description": description,
			"enum": [paramValue],
			#"schema": {
			#	"type": newParamType,
			#},
		}
		if param.attrib.get("optional"):
			paramJson["required"] = False
		return paramJson

	if typeComment:
		description = typeComment + ", " + description

	if "array" in newParamType:
		schema = getListSchema(param, newParamType)
	else:
		schema = {
			"type": newParamType,
		}		
	if paramType == "datetime":
		# %Y-%m-%d %H:%M:%S or %Y-%m-%d %H:%M
		schema["pattern"] = "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}(:[0-9]{2})?$"
	elif paramType == "dict":
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
		schema["properties"] = properties
	paramJson = {}
	if paramName:
		paramJson["name"] = paramName
	paramJson.update({
		"description": description,
		"schema": schema,
	})
	if param.attrib.get("optional"):
		paramJson["required"] = False
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

	jsonMethod = {
		"name": handlerName + "." + methodName,
		"description": method.attrib.get("comment", ""),
		"auth_type": authTypes,
	}
	requires_perm = method.attrib.get("requires_perm")
	if requires_perm:
		jsonMethod["requires_perm"] = requires_perm
	jsonMethod["params"] = params
	outputComment = outputElem.attrib.get("comment", "")
	outputType = outputElem.attrib.get("type")
	outputValue = outputElem.attrib.get("value")
	resultType: "str | None" = None
	resultValues: "list | None" = None
	if outputValue:
		resultValues = [outputValue]
	elif not outputType:
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
		resultType, typeComment = paramTypeMapping[outputType]
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
	resultName = ""
	if resultValues is not None:
		resultName = "Response (one of following values)"
	elif resultType is not None:
		resultName = f"Response ({resultType})"
	result = {
		"name": resultName,
		"comment": outputComment,
	}
	if resultType is not None:
		resultSchema = {
			"title": "",
			"type": resultType,
		}
		if resultParams:
			resultSchema["properties"] = resultParams
		result["schema"] = resultSchema
	if resultValues is not None:
		result["enum"] = resultValues
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
				"version": "1.0.0",
				"title": f"IBSng: branch {branch}: {handlerName}"
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

