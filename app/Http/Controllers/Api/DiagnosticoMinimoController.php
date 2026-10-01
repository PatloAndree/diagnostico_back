<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Diagnostico;
use App\Models\DiagnosticoDetalle;
use App\Models\DiagnosticoTest;
use App\Models\Test;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Process;
use RuntimeException;

class DiagnosticoMinimoController extends Controller
{
    private const PREGUNTAS = [
        ['codigo' => 'animo', 'pregunta' => '¿Cómo calificarías tu estado de ánimo hoy?'],
        ['codigo' => 'sueno', 'pregunta' => '¿Qué tan reparador fue tu sueño reciente?'],
        ['codigo' => 'energia', 'pregunta' => '¿Cómo está tu nivel de energía hoy?'],
        ['codigo' => 'concentracion', 'pregunta' => '¿Qué tan fácil te resulta concentrarte?'],
    ];

    public function formulario(): JsonResponse
    {
        return response()->json([
            'codigo' => 'diagnostico-minimo',
            'nombre' => 'Diagnóstico mínimo de prueba',
            'instruccion' => 'Responde cada pregunta con un valor entero del 1 al 5.',
            'preguntas' => self::PREGUNTAS,
        ]);
    }

    public function ejecutar(Request $request): JsonResponse
    {
        $data = $request->validate([
            'paciente_id' => ['required', 'integer', 'exists:pacientes,id'],
            'respuestas' => ['required', 'array'],
            'respuestas.animo' => ['required', 'integer', 'between:1,5'],
            'respuestas.sueno' => ['required', 'integer', 'between:1,5'],
            'respuestas.energia' => ['required', 'integer', 'between:1,5'],
            'respuestas.concentracion' => ['required', 'integer', 'between:1,5'],
        ]);

        $resultado = $this->ejecutarPython($data);

        $diagnostico = DB::transaction(function () use ($request, $data, $resultado) {
            $test = Test::firstOrCreate(
                ['nombre' => $resultado['test']['nombre'], 'version' => $resultado['test']['version']],
                ['descripcion' => $resultado['test']['descripcion']]
            );

            $diagnostico = Diagnostico::create([
                'paciente_id' => $data['paciente_id'],
                'user_id' => $request->user()->id,
                'fecha' => now(),
                'estado' => 'completado',
                'conclusion' => $resultado['resultado']['conclusion'],
                'observaciones' => $resultado['resultado']['observaciones'],
            ]);

            $diagnosticoTest = DiagnosticoTest::create([
                'diagnostico_id' => $diagnostico->id,
                'test_id' => $test->id,
                'fecha' => now(),
                'puntaje_total' => $resultado['resultado']['puntaje_total'],
                'puntaje_maximo' => $resultado['resultado']['puntaje_maximo'],
                'porcentaje' => $resultado['resultado']['porcentaje'],
            ]);

            foreach ($resultado['detalles'] as $detalle) {
                DiagnosticoDetalle::create([
                    'diagnostico_test_id' => $diagnosticoTest->id,
                    'concepto' => $detalle['concepto'],
                    'respuesta' => (string) $detalle['respuesta'],
                    'puntaje' => $detalle['puntaje'],
                    'puntaje_maximo' => $detalle['puntaje_maximo'],
                    'porcentaje' => $detalle['porcentaje'],
                    'observaciones' => $detalle['observaciones'],
                ]);
            }

            return $diagnostico;
        });

        return response()->json($diagnostico->load('paciente', 'tests.detalles'), 201);
    }

    private function ejecutarPython(array $data): array
    {
        $script = base_path('scripts/diagnostico_minimo.py');
        $proceso = Process::input(json_encode($data, JSON_THROW_ON_ERROR))
            ->timeout(10)
            ->run(['py', '-3', $script]);

        if ($proceso->failed()) {
            throw new RuntimeException('No se pudo ejecutar el diagnóstico de prueba.');
        }

        $resultado = json_decode($proceso->output(), true);

        if (! is_array($resultado)) {
            throw new RuntimeException('El diagnóstico de prueba devolvió una respuesta inválida.');
        }

        return $resultado;
    }
}
