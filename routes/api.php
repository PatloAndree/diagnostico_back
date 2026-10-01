<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\DiagnosticoController;
use App\Http\Controllers\Api\DiagnosticoMinimoController;
use App\Http\Controllers\Api\InstitucionController;
use App\Http\Controllers\Api\PacienteController;
use Illuminate\Support\Facades\Route;

Route::post('login', [AuthController::class, 'login']);

Route::apiResource('instituciones', InstitucionController::class)->parameters([
    'instituciones' => 'institucion',
]);
Route::apiResource('pacientes', PacienteController::class);

Route::get('diagnosticos/minimo/formulario', [DiagnosticoMinimoController::class, 'formulario']);
Route::post('diagnosticos/minimo', [DiagnosticoMinimoController::class, 'ejecutar'])
    ->middleware('auth:sanctum');

Route::get('diagnosticos', [DiagnosticoController::class, 'index'])
    ->middleware('auth:sanctum');
Route::get('diagnosticos/{diagnostico}', [DiagnosticoController::class, 'show'])
    ->middleware('auth:sanctum');
