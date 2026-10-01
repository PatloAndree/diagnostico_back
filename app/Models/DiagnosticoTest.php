<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class DiagnosticoTest extends Model
{
    use HasFactory;

    protected $fillable = [
        'diagnostico_id', 'test_id', 'fecha', 'puntaje_total',
        'puntaje_maximo', 'porcentaje', 'nivel_id',
    ];

    protected function casts(): array
    {
        return ['fecha' => 'datetime'];
    }

    public function diagnostico(): BelongsTo
    {
        return $this->belongsTo(Diagnostico::class);
    }

    public function detalles(): HasMany
    {
        return $this->hasMany(DiagnosticoDetalle::class);
    }

    public function test(): BelongsTo
    {
        return $this->belongsTo(Test::class);
    }
}
