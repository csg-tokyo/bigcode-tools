package com.tuvistavie.astgenerator

import com.tuvistavie.astgenerator.ast.{DotGenerator, JSONGenerator, VocabularyGenerator}
import com.tuvistavie.astgenerator.models._
import com.tuvistavie.astgenerator.trainers.SkipgramTrainer
import com.tuvistavie.astgenerator.util.CliParser
import com.tuvistavie.astgenerator.visualizers.{EmbeddingVisualizer, VocabularyDistributionVisualizer}

object Main {
  def main(args: Array[String]): Unit = {
    CliParser.parse(args) match {
      case Some(config: GenerateAstConfig) =>
        JSONGenerator.run(config)
      case Some(config: ExtractTokensConfig) =>
        // extractTokens(config)
      case Some(config: GenerateDotConfig) =>
        DotGenerator.run(config)
      case Some(config: SkipgramConfig) =>
        SkipgramTrainer.trainSkipgram(config)
      case Some(config: GenerateVocabularyConfig) =>
        VocabularyGenerator.generateProjectVocabulary(config)
      case Some(NoConfig) =>
        CliParser.showUsage()
      case Some(config: VisualizeVocabularyDistributionConfig) =>
        VocabularyDistributionVisualizer.visualizeVocabularyDistribution(config)
      case Some(config: VisualizeEmbeddingsConfig) =>
        EmbeddingVisualizer.visualizeEmbeddings(config)
      case None =>
    }
  }
}
