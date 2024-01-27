#!/usr/bin/python3

import sys
import os
from os.path import (
	dirname,
	join,
	abspath,
	isdir,
	isfile,
)

import json
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Any
import requests

# from datetime import datetime
# from datetime import timedelta
# from dateutil.parser import parse as parse_time

# import dateutil.tz
# from dateutil.tz.tz import tzutc

# try:
# 	from parse import parse as parse_format
# except ModuleNotFoundError as e:
# 	e.msg += f", run `sudo pip3 install parse` to install"
# 	raise e

from prompt_toolkit import prompt as promptLow
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion.word_completer import WordCompleter

branches = ["C", "D", "E"]

homeDir = os.getenv("HOME")
confDir = join(homeDir, ".config", "ibsng-cli")
histDir = join(confDir, "history")
lastPathFile = join(confDir, "last-path")

sessionDir = join(confDir, "auth-tokens")

thisDir = abspath(dirname(__file__))
branchesDir = dirname(thisDir)

os.makedirs(confDir, exist_ok=True)
os.makedirs(histDir, exist_ok=True)
os.makedirs(sessionDir, exist_ok=True)


def dataToPrettyJson(data, ensure_ascii=False, sort_keys=False):
	return json.dumps(
		data,
		sort_keys=sort_keys,
		indent=2,
		ensure_ascii=ensure_ascii,
	)


def prompt(
	message: str,
	multiline: bool = False,
	**kwargs,
):
	text = promptLow(message=message, **kwargs)
	if multiline and text == "!m":
		print("Entering Multi-line mode, press Alt+Enter to end")
		text = promptLow(
			message="",
			multiline=True,
			**kwargs
		)
	return text


def serverAddrIsValid(addr: str) -> bool:
	if "://" not in addr:
		return False
	url = urlparse(addr)
	if not url.scheme:
		return False
	if url.scheme not in ("http", "https"):
		return False
	if not url.netloc:
		return False
	return True


def error(err: str):
	print(err, file=sys.stderr)


def errorExit(err: str):
	print(err, file=sys.stderr)
	sys.exit(1)


@dataclass
class AuthParams:
	auth_type: str
	auth_name: str
	auth_session: str | None
	auth_pass: str | None

	def sessionPath(self, serverHost):
		return join(sessionDir, serverHost, self.auth_type, self.auth_name)

	def toDict(self) -> dict:
		data = {
			"auth_type": self.auth_type,
			"auth_name": self.auth_name,
		}
		if self.auth_session:
			data["auth_session"] = self.auth_session
		else:
			data["auth_pass"] = self.auth_pass


class CLI:
	def __init__(self):
		self.serverURL = None
		self.serverHost = None
		self.auth = None
		self.branch = None
		self.branchDir = None
		self.namespace = None
		self.spec = {}
		self.method = None
		self.params = {}

		self.backToStep = 4
		self.steps = [
			self.step_serverAddr,
			self.step_authParams,
			self.step_branch,
			self.step_namespace,
			self.step_method,
			self.step_paramsAndSend,
		]

	def getServerAddr(self, env=True) -> str:
		if env:
			addr = os.getenv("IBS_ADDR")
			if addr:
				if not serverAddrIsValid(addr):
					errorExit(f"invalid IBS_ADDR={addr!r}")
				return addr
		while True:
			addr = prompt(
				"Server address, for example: 'http://127.0.0.1:1237': ",
				history=FileHistory(join(histDir, "server-addr")),
				auto_suggest=AutoSuggestFromHistory(),
			)
			if addr:
				if serverAddrIsValid(addr):
					return addr
				error("invalid server address: {addr}")

		raise ValueError("server address is not given")

	def getAuthType(self, env=True) -> str:
		if env:
			value = os.getenv("IBS_AUTH_TYPE")
			if value:
				return value
		while True:
			value = prompt(
				"Auth Type: ",
				history=FileHistory(join(histDir, "auth-type")),
				auto_suggest=AutoSuggestFromHistory(),
				completer=WordCompleter(
					["ADMIN", "USER"],
					ignore_case=True,
				)
			)
			if value:
				value = value.upper()
				if value in ("ADMIN", "USER"):
					return value
				error(f"invalid auth_type={value!r}")
		raise ValueError("auth_type is not given")

	def getAuthName(self, env=True) -> str:
		if env:
			value = os.getenv("IBS_AUTH_NAME")
			if value:
				return value
		while True:
			value = prompt(
				"Username: ",
				history=FileHistory(join(histDir, "auth-name")),
				auto_suggest=AutoSuggestFromHistory(),
			)
			if value:
				return value
		raise ValueError("auth_name is not given")

	def getAuthPass(self, env=True) -> str:
		if env:
			password = os.getenv("IBS_AUTH_PASS")
			if password:
				return password
		import getpass
		password = getpass.getpass("Password: ")
		return password

	def readAuthSession(self, auth: AuthParams) -> str | None:
		sessionPath = auth.sessionPath(self.serverHost)
		if not isfile(sessionPath):
			return None
		with open(sessionPath) as _file:
			text = _file.read()
		return text.strip()

	def getAuthParams(self, env=True):
		auth_type = self.getAuthType(env=env)
		auth_name = self.getAuthName(env=env)
		auth = AuthParams(
			auth_type=auth_type,
			auth_name=auth_name,
			auth_session=None,
			auth_pass=None,
		)
		auth_session = self.readAuthSession(auth)
		if auth_session:
			auth.auth_session = auth_session
		else:
			auth.auth_pass = self.getAuthPass(env=env)
		return auth

	def baseCall(self, method: str, **params):
		res = requests.post(
			self.serverURL,
			data=json.dumps({
				"method": method,
				"params": params,
			}),
			headers={
				"content-type": "application/json"
			},
		)
		try:
			response = res.json()
		except Exception as e:
			print(res.text)
			raise e
		error = response.get("error")
		if error:
			print(f"<< ERROR from IBSng: {error}")
			return
		return response["result"]

	def login(self, auth: AuthParams) -> str | None:
		try:
			session_id = self.baseCall(
				"login.login",
				auth_type="ANONYMOUS",
				auth_name="",
				auth_pass="",
				login_auth_type=auth.auth_type,
				login_auth_name=auth.auth_name,
				login_auth_pass=auth.auth_pass,
				auth_remoteaddr="127.0.0.1",
				create_session=True,
			)
		except Exception as e:
			error(f"login failed: {e}")
			return None
		return session_id

	def call(self, method: str, **params):
		auth = self.auth
		if auth.auth_session:
			params["auth_session"] = auth.auth_session
		else:
			params.update({
				"auth_type": auth.auth_type,
				"auth_name": auth.auth_name,
				"auth_pass": auth.auth_pass,
				"auth_remoteaddr": "127.0.0.1",
				"date_type": "gregorian",
			})
		return self.baseCall(method, **params)

	def getBranch(self, env=True):
		if env:
			branch = os.getenv("IBS_BRANCH")
			if branch:
				if branch not in branches:
					errorExit(f"invalid IBS_BRANCH={branch!r}")
				return branch
		while True:
			branch = prompt(
				"Branch: ",
				history=FileHistory(join(histDir, "branch")),
				auto_suggest=AutoSuggestFromHistory(),
				completer=WordCompleter(
					branches,
					ignore_case=True,
				)
			)
			if branch:
				if branch in branches:
					return branch
				branch = branch.upper()
				if branch in branches:
					return branch
				error(f"invalid branch={branch!r}")
		raise ValueError("auth_type is not given")

	def getNamespaceList(self, branchDir) -> list[str]:
		values = []
		for fname in os.listdir(branchDir):
			parts = fname.split(".")
			if len(parts) != 2:
				continue
			if parts[1] != "json":
				continue
			values.append(parts[0])
		return values

	def getNamespace(self, branchDir, env=True) -> str:
		options = self.getNamespaceList(branchDir)
		while True:
			value = prompt(
				"> Namespace: ",
				history=FileHistory(join(histDir, "namespace")),
				auto_suggest=AutoSuggestFromHistory(),
				completer=WordCompleter(
					options,
					ignore_case=True,
				)
			)
			if value:
				if value in options:
					return value
				# the only non-lowercase: SystemNotification
				value = value.lower()
				if value in options:
					return value
				error(f"invalid namespace {value!r}")
		raise ValueError("namespace is not given")

	def getMethod(self) -> str:
		namespace = self.namespace
		prefix = namespace + "."
		options = [
			"r",  # re-send / re-try
			"q",  # quit
		]
		for method in self.spec["methods"]:
			if self.auth.auth_type not in method["auth_type"]:
				continue
			name = method["name"]
			if name.startswith(prefix):
				name = name[len(prefix):]
			options.append(name)
		while True:
			value = prompt(
				">> Method: ",
				history=FileHistory(join(histDir, "method")),
				auto_suggest=AutoSuggestFromHistory(),
				completer=WordCompleter(
					options,
					ignore_case=True,
				)
			)
			if value:
				if value in options:
					return value
				error(f"invalid method {namespace}.{value!r}")
		raise ValueError("method is not given")

	def getMethodSpec(self, methodFull: str):
		spec = self.spec
		for method in spec["methods"]:
			if method["name"] == methodFull:
				return method
		raise ValueError(f"method {methodFull} was not found")

	def step_serverAddr(self, forcePrompt=False):
		self.serverURL = self.getServerAddr(env=not forcePrompt)
		self.serverHost = urlparse(self.serverURL).netloc

	def step_authParams(self, forcePrompt=False):
		auth = self.getAuthParams(env=not forcePrompt)
		if not auth.auth_session:
			session_id = self.login(auth)
			auth.auth_session = session_id
		self.auth = auth

	def step_branch(self, forcePrompt=False):
		self.branch = self.getBranch(env=not forcePrompt)
		branchDir = join(branchesDir, self.branch)
		if not isdir(branchDir):
			errorExit(f"branch dir {branchDir} was not found")
		self.branchDir = branchDir

	def step_namespace(self, forcePrompt=False):
		self.namespace = self.getNamespace(self.branchDir, env=not forcePrompt)
		jsonFile = join(self.branchDir, self.namespace + ".json")
		with open(jsonFile) as _file:
			self.spec = json.load(_file)

	def step_method(self, forcePrompt=False):
		method = self.getMethod()
		if method == "r":  # re-send
			self.resend = True
			return
		if method == "q":  # quit
			sys.exit(0)
		self.method = method
		self.resend = False

	def step_paramsAndSend(self, forcePrompt=False):
		if not (self.namespace and self.method):
			print("<< ERROR: method is not determined")
			return
		methodFull = self.namespace + "." + self.method
		if self.resend:
			params = self.params
		else:
			params = self.askParams(methodFull)
		print("== Request: " + dataToPrettyJson(params))
		res = self.call(methodFull, **params)
		if res is not None:
			print("<< Response: " + dataToPrettyJson(res))

	def askParamObject(self, param: dict, level: int, prefix: str = ""):
		if "properties" in param:
			properties = param["properties"]
		elif "schema" in param and "properties" in param["schema"]:
			properties = param["schema"]["properties"]
		else:
			raise ValueError(f"unexpected param={param}")
		data = {}
		name = param["name"]
		if prefix:
			prefix += "."
		prefix += name + "."
		for propName, prop in properties.items():
			prop["name"] = propName
			try:
				value = self.askParam(
					prop,
					level + 1,
					prefix=prefix + propName,
				)
			except KeyboardInterrupt:
				return data
			if value is None:
				continue
			data[propName] = value
		return data

	def askParamArray(self, param: dict, level: int, prefix: str = ""):
		data = []
		if prefix:
			prefix += "."
		prefix += param["name"]
		index = 0
		while True:
			items = param.get("items")
			if not items:
				print(f"no items in {param}")
				break
			try:
				value = self.askParam(
					items,
					level + 1,
					prefix=prefix + f"[{index}]",
				)
			except KeyboardInterrupt:
				return data
			if value == "":
				break
			data.append(value)
			index += 1
		return data

	def askParam(
		self,
		param: dict,
		level: int,
		prefix: str = "",
	):
		if "schema" in param:
			schema = param["schema"]
		else:
			schema = param

		_type = schema["type"]
		typesDesc = _type
		if isinstance(_type, list):
			typesDesc = " or ".join(_type)
			_type = _type[0]  # FIXME

		if _type == "object":
			return self.askParamObject(param, level, prefix=prefix)

		if _type == "array":
			return self.askParamArray(param, level, prefix=prefix)

		title = ""
		for key in ("name", "title"):
			title = param.get(key, "")
			if title:
				break
			title = schema.get(key, "")
			if title:
				break

		if not title:
			print(f"no title found for {param}")
			return

		titleDesc = title
		for key in ("summary", "description"):
			desc = param.get(key)
			if not desc:
				desc = schema.get(key)
			if desc:
				titleDesc += f" ({desc})"
				break

		promptArgs = {}

		if "enum" in schema:
			values = schema["enum"]
			if isinstance(values, dict):
				values = values.keys()
			promptArgs["completer"] = WordCompleter(
				values,
				ignore_case=True,
			)

		required = param.get("required", True)
		requiredStr = ", required" if required else ""

		histName = "params." + prefix + title
		value = prompt(
			f"{'>' * level} Parameter: {titleDesc} [{typesDesc}{requiredStr}]: ",
			history=FileHistory(join(histDir, histName)),
			auto_suggest=AutoSuggestFromHistory(),
			**promptArgs
		)
		if value == "":
			if required:
				print(f"{'=' * level} Warning: {title} is required")
			return None

		if _type == "number":
			value = float(value)
		elif _type == "integer":
			value = int(value)
		elif _type == "datetime":
			value = int(value)
		elif _type == "boolean":
			value = self.evalBool(value)

		return value

	def evalBool(self, value: str) -> bool | None:
		value = value.lower()
		if value in ("t", "true"):
			return True
		if value in ("f", "false"):
			return False
		try:
			value = int(value)
		except ValueError:
			return bool(value)
		error(f"invalid boolean value {value!r}")
		return None

	def askParams(self, methodFull: str) -> dict[str, Any]:
		methodSpec = self.getMethodSpec(methodFull)
		# print(methodSpec)
		paramsSpec = methodSpec.get("params", [])
		params = {}
		for param in paramsSpec:
			value = self.askParam(param, level=3)
			if value is None:
				continue
			params[param["name"]] = value
		self.params = params
		return params

	def main(self):
		stepN = len(self.steps)
		cancelledStep = -1
		stepI = 0
		while stepI < stepN:
			forcePrompt = stepI < cancelledStep
			try:
				self.steps[stepI](forcePrompt=forcePrompt)
			except KeyboardInterrupt:
				if stepI == 0:
					return
				cancelledStep = stepI
				stepI -= 1
				print()
				continue
			stepI += 1
			if stepI == stepN:
				stepI = self.backToStep


def main():
	cli = CLI()
	cli.main()


if __name__ == "__main__":
	main()
