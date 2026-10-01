<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class DiagnosticoDetalle extends Model
{
    use HasFactory;

    protected $fillable = [
        'diagnostico_test_id', 'concepto', 'respuesta', 'puntaje',
        'puntaje_maximo', 'porcentaje', 'nivel_id', 'observaciones',
    ];

    public function diagnosticoTest(): BelongsTo
    {
        return $this->belongsTo(DiagnosticoTest::class);
    }
}
