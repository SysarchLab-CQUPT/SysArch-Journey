ThisBuild / scalaVersion := "2.13.12"
ThisBuild / version := "0.1.0"
ThisBuild / organization := "sysarch.journey"

val chiselVersion = "6.1.0"

lazy val root = (project in file("."))
  .settings(
    name := "enabled-counter-lab",
    libraryDependencies ++= Seq(
      "org.chipsalliance" %% "chisel" % chiselVersion,
      "edu.berkeley.cs" %% "chiseltest" % "6.0.0" % Test,
      "org.scalatest" %% "scalatest" % "3.2.17" % Test
    ),
    addCompilerPlugin(
      "org.chipsalliance" % "chisel-plugin" % chiselVersion
        cross CrossVersion.full
    ),
    scalacOptions ++= Seq(
      "-deprecation", "-feature", "-language:reflectiveCalls"
    )
  )
