<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\InstitucionController;
use App\Http\Controllers\Api\PacienteController;
use Illuminate\Support\Facades\Route;

Route::post('login', [AuthController::class, 'login']);

Route::apiResource('instituciones', InstitucionController::class)->parameters([
    'instituciones' => 'institucion',
]);
Route::apiResource('pacientes', PacienteController::class);
