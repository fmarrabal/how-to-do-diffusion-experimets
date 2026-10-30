# Progress recovery audit / Auditoría de recuperación del progreso

This separate console probe exercises `Core/Course.cs` read-only. It writes only
new synthetic progress files in a unique Windows temporary directory. It does
not touch a learner's real progress. Its `.cs.audit` extension prevents inclusion
in the independent numerical teaching suite.

Esta consola independiente comprueba `Core/Course.cs` sin modificar su código.
Solo escribe archivos sintéticos nuevos en un directorio temporal único de
Windows. No utiliza el progreso real de estudiantes. La extensión `.cs.audit`
evita incorporarla a la suite numérica independiente.

```powershell
dotnet restore desktop/academy/tests/DiffAtOnce.Academy.Tests/AuditProbes/ProgressAudit.csproj --configfile desktop/academy/tests/DiffAtOnce.Academy.Tests/NuGet.Config
dotnet run --project desktop/academy/tests/DiffAtOnce.Academy.Tests/AuditProbes/ProgressAudit.csproj -c Release --no-restore
```

The output is JSON; exit code 0 means all five recovery assertions pass. Exit
code 1 identifies a reproducible software defect. This does not establish
experimental NMR validation.

La salida es JSON; código 0 significa que pasan las cinco comprobaciones de
recuperación. Código 1 indica un defecto reproducible del software. No constituye
validación experimental de RMN.
