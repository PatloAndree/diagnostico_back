<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Institucion;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class InstitucionController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Institucion::query()->orderBy('nombre')->get());
    }

    public function store(Request $request): JsonResponse
    {
        $institucion = Institucion::create($this->validatedData($request));

        return response()->json($institucion, 201);
    }

    public function show(Institucion $institucion): JsonResponse
    {
        return response()->json($institucion);
    }

    public function update(Request $request, Institucion $institucion): JsonResponse
    {
        $institucion->update($this->validatedData($request, true));

        return response()->json($institucion->fresh());
    }

    public function destroy(Institucion $institucion): JsonResponse
    {
        if ($institucion->pacientes()->exists()) {
            return response()->json([
                'message' => 'No se puede eliminar la institución porque tiene pacientes asociados.',
            ], 409);
        }

        $institucion->delete();

        return response()->json(null, 204);
    }

    private function validatedData(Request $request, bool $isUpdate = false): array
    {
        return $request->validate([
            'nombre' => [$isUpdate ? 'sometimes' : 'required', 'string', 'max:255'],
            'estado' => ['sometimes', 'boolean'],
        ]);
    }
}
