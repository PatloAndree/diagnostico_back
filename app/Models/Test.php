<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Test extends Model
{
    use HasFactory;

    protected $fillable = ['nombre', 'descripcion', 'version'];

    public function diagnosticos(): HasMany
    {
        return $this->hasMany(DiagnosticoTest::class);
    }
}
