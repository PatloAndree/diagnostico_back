<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Diagnostico;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class DiagnosticoController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $filtros = $request->validate([
            'paciente_id' => ['nullable', 'integer', 'exists:pacientes,id'],
            'estado' => ['nullable', 'string', 'max:30'],
        ]);

        $diagnosticos = Diagnostico::query()
            ->with(['paciente', 'usuario', 'tests.test'])
            ->when($filtros['paciente_id'] ?? null, fn ($query, $pacienteId) => $query->where('paciente_id', $pacienteId))
            ->when($filtros['estado'] ?? null, fn ($query, $estado) => $query->where('estado', $estado))
            ->orderByDesc('fecha')
            ->get();

        return response()->json($diagnosticos);
    }

    public function show(Diagnostico $diagnostico): JsonResponse
    {
        return response()->json($diagnostico->load([
            'paciente.institucion',
            'usuario',
            'tests.test',
            'tests.detalles',
        ]));
    }
}
