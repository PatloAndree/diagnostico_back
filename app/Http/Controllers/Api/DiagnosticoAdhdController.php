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
use RuntimeException;

class DiagnosticoAdhdController extends Controller
{
    public function ejecutar(Request $request): JsonResponse
    {
        $reglas = [
            'paciente_id' => ['required', 'integer', 'exists:pacientes,id'],
            'respuestas' => ['required', 'array'],
        ];

        for ($numero = 1; $numero <= 18; $numero++) {
            $reglas["respuestas.item_{$numero}"] = ['required', 'integer', 'between:0,3'];
        }

        $data = $request->validate($reglas);
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
        $rutaScript = base_path('scripts/diagnosticar_adhd.py');
        $entrada = base64_encode(json_encode($data, JSON_THROW_ON_ERROR));

        // "python" debe apuntar al mismo intérprete de Python 3 donde se
        // instalaron numpy y scikit-learn. El JSON se codifica en Base64 para
        // no exponer el comando a caracteres de las respuestas del usuario.
        $comando = sprintf(
            'python %s %s 2>&1',
            escapeshellarg($rutaScript),
            escapeshellarg($entrada),
        );
        $salida = shell_exec($comando);
        $resultado = json_decode($salida ?? '', true);

        if (! is_array($resultado)) {
            throw new RuntimeException(trim($salida ?: '') ?: 'No se pudo ejecutar el tamizaje ADHD.');
        }
        if (isset($resultado['error'])) {
            throw new RuntimeException($resultado['error']);
        }

        return $resultado;
    }
}
