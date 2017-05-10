package com.tuvistavie.astgenerator

import java.io.File
import java.nio.file.{Path, Paths}

import com.fasterxml.jackson.databind.node.JsonNodeFactory
import com.fasterxml.jackson.databind.{JsonNode, ObjectMapper, ObjectWriter}
import com.tuvistavie.astgenerator.util.{CliParser, FileUtils}

object Main {
  def processFile(path: Path, config: Config): JsonNode = {
    val processor = FileProcessor(path, config)
    processor.run()
    processor.toJson
  }

  def makeWriter(config: Config): ObjectWriter = {
    val mapper = new ObjectMapper()
    if (config.pretty) mapper.writerWithDefaultPrettyPrinter() else mapper.writer()
  }

  def makeOutput(config: Config, result: JsonNode): JsonNode = {
    val output = JsonNodeFactory.instance.objectNode()
    output.put("project", config.project)
    output.put("version", Config.formatVersion)
    output.set("result", result)
    output
  }

  def processProject(config: Config): Unit = {
    val files = FileUtils.findFiles(config.project, FileUtils.withExtension("java"))
    val projectPath = Paths.get(config.project)
    val result = JsonNodeFactory.instance.objectNode()
    files map { f => (f, processFile(f, config)) } foreach {
      case (f, r) => result.set(projectPath.relativize(f).toString, r)
    }
    val writer = makeWriter(config)
    val outputFile = new File(config.output)
    val output = makeOutput(config, result)
    writer.writeValue(outputFile, output)
  }

  def main(args: Array[String]): Unit = {
    CliParser.parse(args) match {
      case Some(config) =>
        processProject(config)
      case None =>
    }
  }
}
