package dev.otel.demo.worker

import io.opentelemetry.api.OpenTelemetry
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator
import io.opentelemetry.context.propagation.ContextPropagators
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter
import io.opentelemetry.sdk.OpenTelemetrySdk
import io.opentelemetry.sdk.resources.Resource
import io.opentelemetry.sdk.trace.SdkTracerProvider
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor

fun initOpenTelemetry(serviceName: String, otlpEndpoint: String): OpenTelemetry {
    val disableTracing = System.getenv("OTEL_DISABLE_TRACING")?.lowercase() in setOf("true", "1")
    val tracerProviderBuilder = SdkTracerProvider.builder()
        .setResource(Resource.getDefault().toBuilder().put("service.name", serviceName).build())
    if (!disableTracing) {
        val spanExporter = OtlpGrpcSpanExporter.builder()
            .setEndpoint(otlpEndpoint)
            .build()
        tracerProviderBuilder.addSpanProcessor(BatchSpanProcessor.builder(spanExporter).build())
    }
    val tracerProvider = tracerProviderBuilder.build()
    return OpenTelemetrySdk.builder()
        .setTracerProvider(tracerProvider)
        .setPropagators(ContextPropagators.create(W3CTraceContextPropagator.getInstance()))
        .buildAndRegisterGlobal()
}
