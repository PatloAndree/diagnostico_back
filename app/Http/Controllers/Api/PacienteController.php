<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Paciente;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class PacienteController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Paciente::query()->with('institucion')->orderBy('apellidos')->orderBy('nombres')->get());
    }

    public function store(Request $request): JsonResponse
    {
        $paciente = Paciente::create($this->validatedData($request));

        return response()->json($paciente->load('institucion'), 201);
    }

    public function show(Paciente $paciente): JsonResponse
    {
        return response()->json($paciente->load('institucion'));
    }

    public function update(Request $request, Paciente $paciente): JsonResponse
    {
        $paciente->update($this->validatedData($request, $paciente));

        return response()->json($paciente->fresh()->load('institucion'));
    }

    public function destroy(Paciente $paciente): JsonResponse
    {
        $paciente->delete();

        return response()->json(null, 204);
    }

    private function validatedData(Request $request, ?Paciente $paciente = null): array
    {
        $isUpdate = $paciente !== null;

        return $request->validate([
            'institucion_id' => [$isUpdate ? 'sometimes' : 'nullable', 'nullable', 'integer', 'exists:instituciones,id'],
            'nombres' => [$isUpdate ? 'sometimes' : 'required', 'string', 'max:255'],
            'apellidos' => [$isUpdate ? 'sometimes' : 'required', 'string', 'max:255'],
            'documento' => [
                'nullable',
                'string',
                'max:30',
                Rule::unique('pacientes', 'documento')->ignore($paciente),
            ],
            'fecha_nacimiento' => [$isUpdate ? 'sometimes' : 'required', 'date', 'before_or_equal:today'],
        ]);
    }
}
