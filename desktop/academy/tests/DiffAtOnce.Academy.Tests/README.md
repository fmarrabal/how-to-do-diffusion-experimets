# Native teaching model QA / QA de modelos didácticos nativos

No test package or production mathematics dependency is required. These console checks compile the actual Core project and exercise the native C# calculators. They do not validate WPF rendering, a spectrometer, or experimental data.

No se necesita un paquete de pruebas ni una dependencia matemática de producción. Estas pruebas de consola compilan el proyecto Core real y ejercitan los calculadores C#. No validan la interfaz WPF, un espectrómetro ni datos experimentales.

From the workspace root / Desde la raíz:

```powershell
dotnet restore desktop/academy/tests/DiffAtOnce.Academy.Tests/DiffAtOnce.Academy.Tests.csproj --configfile desktop/academy/tests/DiffAtOnce.Academy.Tests/NuGet.Config
dotnet run --project desktop/academy/tests/DiffAtOnce.Academy.Tests/DiffAtOnce.Academy.Tests.csproj -c Release --no-restore -- --report desktop/academy/tests/DiffAtOnce.Academy.Tests/teaching-simulations-qa.json
```

The local NuGet configuration disables all external package sources. Installed .NET 8 reference packs are required. The Codex execution sandbox on this machine denied access to the global NuGet configuration even with an explicit local configuration; a normal authorized local restore succeeded, then the build and tests ran in the sandbox without restore. No packages were downloaded or installed.

La configuración local de NuGet deshabilita todas las fuentes externas. Se requieren los paquetes de referencia de .NET 8 ya instalados. La restauración local no descargó ni instaló paquetes.

The report includes the SHA-256 of `TeachingSimulations.cs` and numerical evidence. Important checks include:

- Signed 22 µs first-null example: P90=11 µs; the next 44 µs null is not P180.
- Independent numerical integration of q(t)² versus rectangular PGSE and general piecewise-constant effective gradients; longitudinal storage preserves q.
- Standard-based gradient scale and the 10% gradient → 21% D error identity.
- Reproducible seeded noise; an ignored baseline yields R²≈0.9985 while D is about 10% too low.
- Fixed-velocity phase versus magnitude and uniform velocity-distribution sinc, checked by numerical velocity quadrature.
- ILT energy/rank invariants, ambiguity of two candidate distributions, and independent NumPy singular-value reference.

`ilt-numpy-reference.json` was generated once with existing NumPy 2.5.1 using:

```python
b = numpy.linspace(0, 3, 32)
d = 0.1 * numpy.power(30, numpy.linspace(0, 1, 40))
K = numpy.exp(-b[:, None] * d[None, :]) / numpy.sqrt(32)
reference = numpy.linalg.svd(K, compute_uv=False)[:7]
```

NumPy is not needed to run the console suite. Only the seven well-resolved leading singular values are compared; the production Gram/Jacobi method explicitly reports its unresolved tail below a relative 1e-7 floor. No exact full condition number or ILT reconstruction is claimed.

NumPy no es necesario para ejecutar las pruebas. Sólo se comparan siete valores singulares iniciales bien resueltos. El método Gram/Jacobi declara no resuelta la cola relativa inferior a 1e-7. No se afirma un número de condición completo exacto ni una reconstrucción ILT.
