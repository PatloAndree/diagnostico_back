<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Diagnostico extends Model
{
    use HasFactory;

    protected $table = 'diagnostico';

    protected $fillable = [
        'paciente_id',
        'user_id',
        'fecha',
        'estado',
        'nivel_id',
        'conclusion',
        'observaciones',
    ];

    protected function casts(): array
    {
        return ['fecha' => 'datetime'];
    }

    public function paciente(): BelongsTo
    {
        return $this->belongsTo(Paciente::class);
    }

    public function usuario(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id');
    }

    public function tests(): HasMany
    {
        return $this->hasMany(DiagnosticoTest::class);
    }
}
