#!/bin/sh
set -e
APP_HOME=$( cd "$(dirname "$0")" && pwd -P )
CLASSPATH=$APP_HOME/gradle/wrapper/gradle-wrapper.jar
if [ ! -r "$CLASSPATH" ]; then
  echo "Gradle wrapper jar not found. Run: gradle wrapper"
  exit 1
fi
exec java -cp "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
