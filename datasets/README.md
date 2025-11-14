# Dataset Management

This directory contains dataset configuration and versioning information for the MLOps music recommendation system.

## Files

- **`dataset-version.txt`** - Current dataset version (semantic versioning)
- **`dataset-config.yaml`** - Dataset configuration including URL, validation rules, and training parameters
- **`README.md`** - This documentation file

## Dataset Versioning Strategy

We use **semantic versioning** (MAJOR.MINOR.PATCH) for datasets:

- **MAJOR** (1.x.x): Breaking changes - dataset structure changes, column removals, format changes
- **MINOR** (x.1.x): New features - new columns added, additional data, backward compatible
- **PATCH** (x.x.1): Bug fixes - data corrections, quality improvements, no structural changes

### Current Version: 1.0.0

## How to Update Dataset

### Method 1: Update Dataset URL (Recommended)
1. Upload new dataset to your data repository
2. Update the `url` field in `dataset-config.yaml`
3. Update the `version` field in both files
4. Add update entry in `dataset-config.yaml` under `updates` section
5. Commit and push changes

```bash
# Update version
echo "1.1.0" > datasets/dataset-version.txt

# Edit dataset-config.yaml with new URL and version

# Commit changes
git add datasets/
git commit -m "feat: update dataset to v1.1.0"
git push
```

This will automatically:
- Trigger CI/CD pipeline
- Trigger training service to retrain model
- ArgoCD will sync changes
- New model will be generated

### Method 2: Manual Training Trigger
If you want to retrain without changing the dataset:

```bash
curl -X POST http://<training-service-url>:5005/train \
  -H "Content-Type: application/json" \
  -d '{"dataset_url": "https://your-dataset-url.csv"}'
```

## Dataset Format

### Expected CSV Structure
```csv
pid,track_name,artist_name
1,Song A,Artist A
1,Song B,Artist B
1,Song C,Artist C
2,Song B,Artist B
2,Song D,Artist D
...
```

### Requirements
- **Format:** CSV with comma delimiter
- **Encoding:** UTF-8
- **Required Columns:** `pid`, `track_name`, `artist_name`
- **Minimum:** 100 playlists with at least 2 songs each

## Dataset Validation

The training service validates datasets against these criteria:
- Minimum number of playlists
- Minimum songs per playlist
- Required columns present
- Proper encoding
- No empty values in required fields

## Version History

| Version | Date | Description | Author |
|---------|------|-------------|--------|
| 1.0.0 | 2025-11-14 | Initial dataset version - Spotify ds1 | caiogrossi |

## Integration with CI/CD

When dataset files are updated:

1. **GitHub Actions** detects changes to `datasets/` directory
2. **Dataset Update Workflow** is triggered
3. Validates dataset version format
4. Triggers **Training Service CI/CD** workflow
5. **ArgoCD** detects manifest changes and syncs
6. **Training Service** retrains model with new dataset
7. **Recommendation Service** automatically loads new model

## Configuration Parameters

### Training Parameters
Defined in `dataset-config.yaml`:
- `min_support`: Minimum support for association rules (default: 0.05)
- `min_confidence`: Minimum confidence for association rules (default: 0.3)
- `test_size`: Train-test split ratio (default: 0.2)
- `random_state`: Random seed for reproducibility (default: 42)

### Validation Rules
- `min_playlists`: Minimum playlists required (default: 100)
- `min_songs_per_playlist`: Minimum songs per playlist (default: 2)
- `required_columns`: Must have columns for pid, track_name, artist_name

## Best Practices

1. **Always increment version** when updating dataset
2. **Document changes** in `dataset-config.yaml` updates section
3. **Test dataset locally** before pushing
4. **Validate format** matches expected structure
5. **Use meaningful version numbers** based on change significance
6. **Keep update history** for audit trail
7. **Monitor training** after dataset updates
8. **Backup old datasets** for rollback capability

## Data Privacy & Security

- Ensure datasets comply with privacy regulations
- Do not commit sensitive or personal data
- Use secure URLs (HTTPS) for dataset sources
- Consider data anonymization for public repositories

## Support

For questions about dataset management:
- Check training service logs: `kubectl logs -n caiogrossi -l app=caiogrossi-recommender-trainer`
- Review ArgoCD sync status
- Verify GitHub Actions workflow runs
- Check model metadata: `GET /health` on training service
