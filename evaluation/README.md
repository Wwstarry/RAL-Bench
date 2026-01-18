# 通用评估框架文档

## 1. 框架概述

本评估框架旨在为所有项目提供一致的功能测试和5种非功能测试，确保生成的代码质量和性能达到参考仓库的标准。

### 支持的测试类型

- **功能测试 (Functional Testing)**: 验证生成的代码是否实现了预期的功能
- **性能测试 (Performance Testing)**: 测量代码的执行效率
- **资源测试 (Resource Testing)**: 评估内存和CPU使用情况
- **健壮性测试 (Robustness Testing)**: 测试代码在异常条件下的表现
- **安全性测试 (Security Testing)**: 检查代码中的安全漏洞
- **可维护性测试 (Maintainability Testing)**: 评估代码的可读性和可维护性

## 2. 框架结构

```
├── evaluation/
│   ├── measure_reference.py      # 为参考仓库收集基线指标
│   ├── measure_generated.py      # 评估生成的代码仓库
│   └── README.md                 # 本文档
├── tasks/                        # 项目任务配置文件
│   └── <ProjectName>/
│       └── <project_name>.yaml
├── repositories/                 # 参考仓库
│   └── <ProjectName>/
├── generation/                   # 生成的代码仓库
│   └── <ProjectName>/
└── tests/                        # 测试套件
    └── <ProjectName>/
        ├── functional_test.py
        ├── performance_test.py
        ├── resource_test.py
        ├── robustness_test.py
        ├── security_test.py
        └── maintainability_test.py
```

## 3. 为新项目配置评估

### 3.1 创建任务配置文件

在 `tasks/<ProjectName>/` 目录下创建 `<project_name>.yaml` 文件，包含以下内容：

```yaml
task_id: <project_id>
domain: <domain>
difficulty: <difficulty>
description: "<项目描述>"
interfaces:
  type: <LIB/CLI/API>
  language: python
  entry_point: <entry_point>
reference_repository: ./repositories/<ProjectName>
generated_repository: ./generation/<ProjectName>
test_suite:
  functional: ./tests/<ProjectName>/functional_test.py
  performance: ./tests/<ProjectName>/performance_test.py
  resource: ./tests/<ProjectName>/resource_test.py
  robustness: ./tests/<ProjectName>/robustness_test.py
  security: ./tests/<ProjectName>/security_test.py
  maintainability: ./tests/<ProjectName>/maintainability_test.py
baseline_metrics: {}
```

### 3.2 创建测试套件

在 `tests/<ProjectName>/` 目录下创建以下测试文件：

1. `functional_test.py`: 功能测试
2. `performance_test.py`: 性能测试
3. `resource_test.py`: 资源测试
4. `robustness_test.py`: 健壮性测试
5. `security_test.py`: 安全性测试
6. `maintainability_test.py`: 可维护性测试

### 3.3 测试文件要求

所有测试文件必须：

- 使用 pytest 框架编写
- 支持通过环境变量 `<PROJECTNAME>_TARGET` 选择测试目标（reference/generated）
- 遵循与参考仓库相同的测试接口

## 4. 收集基线指标

使用 `measure_reference.py` 为参考仓库收集基线指标：

```bash
python evaluation/measure_reference.py --task tasks/<ProjectName>/<project_name>.yaml --target-env <PROJECTNAME>_TARGET
```

例如，为 Stegano 项目收集基线指标：

```bash
python evaluation/measure_reference.py --task tasks/Stegano/stegano.yaml --target-env STEGANO_TARGET
```

这将运行所有测试套件，并将基线指标保存到任务配置文件的 `baseline_metrics` 字段中。

## 5. 评估生成的代码

使用 `measure_generated.py` 评估生成的代码仓库：

```bash
python evaluation/measure_generated.py tasks/<ProjectName>/<project_name>.yaml generation/<ProjectName> [results/<ProjectName>_results.yaml]
```

例如，评估生成的 Stegano 代码：

```bash
python evaluation/measure_generated.py tasks/Stegano/stegano.yaml generation/Stegano results/Stegano_results.yaml
```

这将：

1. 加载任务配置文件和基线指标
2. 在生成的代码仓库上运行所有测试套件
3. 计算每个测试类型的得分
4. 计算总分（加权平均）
5. 将结果保存到指定的输出文件

## 6. 得分计算方法

### 6.1 功能测试得分

```
功能测试得分 = 通过的测试数量 / 总测试数量
```

### 6.2 性能测试得分

```
性能测试得分 = 基线执行时间 / 实际执行时间
```

### 6.3 资源测试得分

```
内存得分 = 基线内存使用 / 实际内存使用
CPU得分 = 基线CPU使用 / 实际CPU使用
资源测试得分 = (内存得分 + CPU得分) / 2
```

### 6.4 健壮性、安全性和可维护性测试得分

```
得分 = 通过的测试数量 / 总测试数量
```

### 6.5 总分

```
总分 = (功能测试得分 × 0.4) + (性能测试得分 × 0.15) + (资源测试得分 × 0.15) + 
       (健壮性测试得分 × 0.1) + (安全性测试得分 × 0.1) + (可维护性测试得分 × 0.1)
```

## 7. 结果解释

评估结果包含：

- **测试结果**：每个测试套件的详细执行结果
- **得分**：每个测试类型的得分（0-1）
- **总分**：综合得分（0-1）

### 得分解释

- **1.0**：完美匹配参考仓库
- **0.9-0.99**：优秀
- **0.8-0.89**：良好
- **0.7-0.79**：一般
- **0.6-0.69**：及格
- **<0.6**：不及格

## 8. 最佳实践

1. **测试一致性**：确保生成的代码与参考仓库使用相同的API接口
2. **测试覆盖**：尽可能提高测试覆盖率
3. **基线更新**：如果参考仓库有重大更新，重新收集基线指标
4. **性能优化**：优先关注性能和资源使用情况
5. **安全考虑**：确保代码没有已知的安全漏洞
6. **可维护性**：编写清晰、模块化的代码

## 9. 常见问题

### 9.1 测试失败

- 检查生成的代码是否与参考仓库API兼容
- 确保所有依赖都已安装
- 查看测试输出的详细错误信息

### 9.2 性能得分低

- 分析代码中的性能瓶颈
- 优化算法和数据结构
- 减少不必要的计算和I/O操作

### 9.3 资源使用高

- 优化内存管理
- 减少CPU密集型操作
- 避免内存泄漏

## 10. 示例

### 为Stegano项目收集基线指标

```bash
python evaluation/measure_reference.py --task tasks/Stegano/stegano.yaml --target-env STEGANO_TARGET
```

### 评估生成的Stegano代码

```bash
python evaluation/measure_generated.py tasks/Stegano/stegano.yaml generation/Stegano
```

## 11. 联系方式

如有任何问题或建议，请联系项目负责人。