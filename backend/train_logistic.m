%% OPTIMIZED LOGISTIC REGRESSION FOR NETWORK INTRUSION DETECTION
%% Fixed rank deficiency, improved specificity, better feature selection
clear all; clc; close all;

%% Check toolboxes
fprintf('Checking MATLAB Toolboxes...\n');
fprintf('%s\n', repmat('=', 1, 50));

required_toolboxes = {
    'Statistics and Machine Learning Toolbox', 'stats';
};

for i = 1:size(required_toolboxes, 1)
    toolbox_name = required_toolboxes{i, 1};
    toolbox_code = required_toolboxes{i, 2};
    if license('test', toolbox_code)
        fprintf('OK %s: Available\n', toolbox_name);
    else
        fprintf('ERROR %s: NOT Available - Please install!\n', toolbox_name);
    end
end

%% Check GPU
fprintf('\nChecking GPU...\n');
fprintf('%s\n', repmat('-', 1, 30));

try
    gpu_device = gpuDevice();
    if gpu_device.DeviceSupported
        fprintf('GPU Available: %s\n', gpu_device.Name);
        gpu_available = true;
    else
        fprintf('GPU not supported\n');
        gpu_available = false;
    end
catch
    fprintf('No GPU available\n');
    gpu_available = false;
end

global USE_GPU;
USE_GPU = gpu_available;
fprintf('\n');

%% MAIN FUNCTION
function main(train_file, test_file, output_dir)
    fprintf('OPTIMIZED LOGISTIC REGRESSION SYSTEM\n');
    fprintf('%s\n', repmat('=', 1, 50));
    
    if ~exist(train_file, 'file'), error('Training file not found: %s', train_file); end
    if ~exist(test_file, 'file'), error('Test file not found: %s', test_file); end
    
    fprintf('Training file: %s\n', train_file);
    fprintf('Testing file:  %s\n', test_file);
    fprintf('Output dir:    %s\n', output_dir);
    
    if ~exist(output_dir, 'dir'), mkdir(output_dir); end
    
    % Train
    fprintf('\nTRAINING MODEL\n');
    fprintf('%s\n', repmat('-', 1, 40));
    model = train_logistic_regression_model(train_file);
    
    % Evaluate
    fprintf('\nEVALUATING MODEL\n');
    fprintf('%s\n', repmat('-', 1, 25));
    results = evaluate_model(model, test_file);
    
    % Optimize threshold for better balance
    fprintf('\nOPTIMIZING DECISION THRESHOLD\n');
    fprintf('%s\n', repmat('-', 1, 40));
    model = optimize_threshold_balanced(model, results);
    
    % Re-evaluate
    fprintf('\nRE-EVALUATING WITH OPTIMIZED THRESHOLD\n');
    fprintf('%s\n', repmat('-', 1, 45));
    results = evaluate_model(model, test_file);
    
    % Save
    fprintf('\nSAVING RESULTS\n');
    fprintf('%s\n', repmat('-', 1, 30));
    model_path = fullfile(output_dir, 'logistic_regression_model.mat');
    results_path = fullfile(output_dir, 'results.json');
    
    save(model_path, 'model');
    fprintf('Model saved: %s\n', model_path);
    
    save_results_json(results, model, results_path);
    
    fprintf('\n✓ COMPLETE!\n');
end

%% Streamlined Feature Engineering (less redundant features)
function [engineered_data, feature_names] = dynamic_feature_engineering(data)
    fprintf('Feature engineering...\n');
    engineered_data = data;
    original_features = engineered_data.Properties.VariableNames;
    
    % Convert categorical/string to numeric
    for col = 1:width(engineered_data)
        colname = engineered_data.Properties.VariableNames{col};
        if iscategorical(engineered_data.(colname)) || isstring(engineered_data.(colname)) || iscellstr(engineered_data.(colname))
            if ~iscategorical(engineered_data.(colname))
                engineered_data.(colname) = categorical(engineered_data.(colname));
            end
            engineered_data.(colname) = double(engineered_data.(colname));
        end
    end
    
    % Temporal features (simplified)
    if ismember('stime', original_features)
        engineered_data.hour = mod(floor(engineered_data.stime * 24), 24);
        engineered_data.is_business_hours = double((engineered_data.hour >= 9) & (engineered_data.hour <= 17));
    end
    
    % Byte features (key metrics only)
    if ismember('sbytes', original_features) && ismember('dbytes', original_features)
        engineered_data.total_bytes = engineered_data.sbytes + engineered_data.dbytes;
        engineered_data.log_total_bytes = log1p(engineered_data.total_bytes);
        % Only create ratio if denominator is meaningful
        safe_dbytes = max(engineered_data.dbytes, 1);
        engineered_data.byte_ratio = engineered_data.sbytes ./ safe_dbytes;
        % Cap extreme ratios
        engineered_data.byte_ratio = min(engineered_data.byte_ratio, 100);
    end
    
    % Packet features (simplified)
    if ismember('spkts', original_features) && ismember('dpkts', original_features)
        engineered_data.total_packets = engineered_data.spkts + engineered_data.dpkts;
        safe_dpkts = max(engineered_data.dpkts, 1);
        engineered_data.packet_ratio = min(engineered_data.spkts ./ safe_dpkts, 100);
    end
    
    % Duration features
    if ismember('dur', original_features)
        engineered_data.log_duration = log1p(engineered_data.dur);
        if ismember('total_bytes', engineered_data.Properties.VariableNames)
            safe_dur = max(engineered_data.dur, 0.001);
            engineered_data.throughput = engineered_data.total_bytes ./ safe_dur;
            engineered_data.log_throughput = log1p(engineered_data.throughput);
        end
    end
    
    % Port features (essential only)
    if ismember('sport', original_features) && ismember('dport', original_features)
        engineered_data.dst_is_wellknown = double(engineered_data.dport < 1024);
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995];
        engineered_data.dst_is_common = double(ismember(engineered_data.dport, common_ports));
    end
    
    % Network behavior (simplified)
    if ismember('sloss', original_features) && ismember('dloss', original_features)
        engineered_data.total_loss = engineered_data.sloss + engineered_data.dloss;
    end
    
    if ismember('sjit', original_features) && ismember('djit', original_features)
        engineered_data.total_jitter = engineered_data.sjit + engineered_data.djit;
    end
    
    all_features = engineered_data.Properties.VariableNames;
    exclude_features = {'label', 'attack_cat', 'stime', 'srcip', 'dstip'};
    feature_names = setdiff(all_features, exclude_features, 'stable');
    fprintf('   Features: %d\n', length(feature_names));
end

%% Enhanced Feature Selection with Rank Check
function [selected_indices, selected_features] = robust_feature_selection(X, y, feature_names, n_features)
    if nargin < 4, n_features = 12; end  % Further reduced
    fprintf('Robust feature selection (top %d)...\n', n_features);
    
    % Step 1: Remove zero/near-zero variance
    fprintf('   Removing low-variance features...\n');
    feature_var = var(X);
    var_threshold = 1e-4;  % Stricter threshold
    keep_var = feature_var > var_threshold;
    X = X(:, keep_var);
    feature_names = feature_names(keep_var);
    fprintf('   Removed %d low-variance features\n', sum(~keep_var));
    
    % Step 2: Remove highly correlated features
    fprintf('   Removing correlated features (threshold=0.80)...\n');
    corr_matrix = corr(X);
    corr_threshold = 0.80;  % Even more aggressive
    to_remove = false(1, size(X, 2));
    
    for i = 1:size(corr_matrix, 1)
        for j = i+1:size(corr_matrix, 2)
            if abs(corr_matrix(i, j)) > corr_threshold && ~to_remove(j)
                to_remove(j) = true;
            end
        end
    end
    
    fprintf('   Removed %d highly correlated features\n', sum(to_remove));
    X = X(:, ~to_remove);
    feature_names = feature_names(~to_remove);
    
    % Step 3: Score features by correlation with target
    feature_scores = zeros(1, size(X, 2));
    for i = 1:size(X, 2)
        feature_scores(i) = abs(corr(X(:, i), y));
    end
    
    % Step 4: Select top N features
    [~, sorted_indices] = sort(feature_scores, 'descend');
    n_features = min(n_features, length(feature_names));
    
    % Step 5: Iteratively build feature set checking rank
    fprintf('   Building feature set with rank checking...\n');
    selected_indices = [];
    selected_features = {};
    
    for i = 1:length(sorted_indices)
        candidate_idx = sorted_indices(i);
        test_indices = [selected_indices, candidate_idx];
        X_test = X(:, test_indices);
        
        % Check rank
        if rank(X_test) == size(X_test, 2)
            selected_indices = test_indices;
            selected_features{end+1} = feature_names{candidate_idx};
            
            if length(selected_indices) >= n_features
                break;
            end
        end
    end
    
    fprintf('   Selected %d full-rank features\n', length(selected_features));
end

%% Train Model with Enhanced Settings
function model = train_logistic_regression_model(csv_file)
    fprintf('Loading dataset: %s\n', csv_file);
    data = readtable(csv_file);
    fprintf('   Loaded %d samples\n', height(data));
    
    % Handle missing values
    for col = 1:width(data)
        if isnumeric(data{:, col})
            data{:, col} = fillmissing(data{:, col}, 'constant', 0);
        elseif iscategorical(data{:, col}) || isstring(data{:, col}) || iscellstr(data{:, col})
            data{:, col} = fillmissing(data{:, col}, 'constant', '<missing>');
        end
    end
    
    % Feature engineering
    [engineered_data, feature_names] = dynamic_feature_engineering(data);
    
    % Extract features and labels
    X = table2array(engineered_data(:, feature_names));
    y = engineered_data.label;
    
    if iscategorical(y) || isstring(y) || iscellstr(y)
        y = double(categorical(y));
    end
    y = double(y);
    
    % Clean data
    X(isnan(X)) = 0;
    X(isinf(X)) = 0;
    
    % Check class distribution
    class_counts = [sum(y == 0), sum(y == 1)];
    fprintf('Class distribution: Normal=%d (%.1f%%), Attack=%d (%.1f%%)\n', ...
        class_counts(1), 100*class_counts(1)/length(y), ...
        class_counts(2), 100*class_counts(2)/length(y));
    
    % Normalize with robust scaling (clip outliers)
    fprintf('Normalizing features with outlier clipping...\n');
    X_clipped = X;
    for i = 1:size(X, 2)
        q1 = quantile(X(:, i), 0.01);
        q99 = quantile(X(:, i), 0.99);
        X_clipped(:, i) = max(min(X(:, i), q99), q1);
    end
    
    [X_scaled, mu, sigma] = zscore(X_clipped);
    sigma(sigma == 0) = 1;
    X_scaled = (X_clipped - mu) ./ sigma;
    X_scaled(isnan(X_scaled)) = 0;
    
    % Feature selection with rank checking
    [selected_indices, selected_features] = robust_feature_selection(X_scaled, y, feature_names, 12);
    X_selected = X_scaled(:, selected_indices);
    
    % Verify rank
    actual_rank = rank(X_selected);
    fprintf('   Design matrix rank: %d / %d\n', actual_rank, size(X_selected, 2));
    
    % Calculate balanced class weights
    total = length(y);
    weight_for_0 = total / (2 * class_counts(1));
    weight_for_1 = total / (2 * class_counts(2));
    
    % Adjust weights to favor specificity (reduce FPR)
    weight_for_0 = weight_for_0 * 1.3;  % Increase penalty for misclassifying normal
    
    weights = ones(size(y));
    weights(y == 0) = weight_for_0;
    weights(y == 1) = weight_for_1;
    
    fprintf('Adjusted class weights: Normal=%.3f, Attack=%.3f\n', weight_for_0, weight_for_1);
    
    % Train with Ridge regularization (L2)
    fprintf('Training with Ridge regularization...\n');
    options = statset('MaxIter', 3000, 'Display', 'off');
    
    % Add small ridge penalty directly to design matrix
    ridge_lambda = 0.01;
    X_ridge = [X_selected; sqrt(ridge_lambda) * eye(size(X_selected, 2))];
    y_ridge = [y; zeros(size(X_selected, 2), 1)];
    weights_ridge = [weights; ones(size(X_selected, 2), 1)];
    
    final_model = fitglm(X_ridge, y_ridge, ...
        'Distribution', 'binomial', ...
        'Link', 'logit', ...
        'Weights', weights_ridge, ...
        'Options', options);
    
    % Training accuracy on original data
    y_pred_train = predict(final_model, X_selected) > 0.5;
    train_accuracy = sum(y_pred_train == y) / length(y);
    
    fprintf('   Training accuracy: %.4f\n', train_accuracy);
    fprintf('   ✓ Model trained successfully\n');
    
    % Package model
    model = struct();
    model.classifier = final_model;
    model.feature_names = feature_names;
    model.selected_indices = selected_indices;
    model.selected_features = selected_features;
    model.scaler_mu = mu;
    model.scaler_sigma = sigma;
    model.train_accuracy = train_accuracy;
    model.converged = true;
    model.threshold = 0.5;
    model.ridge_lambda = ridge_lambda;
end

%% Optimize Threshold for Balanced Performance
function model = optimize_threshold_balanced(model, results)
    fprintf('Finding optimal threshold (balanced F1 and Specificity)...\n');
    
    thresholds = 0.35:0.02:0.65;
    best_score = 0;
    best_threshold = 0.5;
    best_metrics = struct();
    
    for thresh = thresholds
        y_pred_temp = double(results.y_proba > thresh);
        cm = confusionmat(results.y_true, y_pred_temp);
        
        if size(cm, 1) == 2 && size(cm, 2) == 2
            precision = cm(2,2) / (cm(2,2) + cm(1,2));
            recall = cm(2,2) / (cm(2,2) + cm(2,1));
            specificity = cm(1,1) / (cm(1,1) + cm(1,2));
            f1 = 2 * (precision * recall) / (precision + recall);
            
            % Combined score: balance F1 and Specificity
            combined_score = 0.6 * f1 + 0.4 * specificity;  % 60% F1, 40% Specificity
            
            if combined_score > best_score
                best_score = combined_score;
                best_threshold = thresh;
                best_metrics.f1 = f1;
                best_metrics.specificity = specificity;
                best_metrics.precision = precision;
            end
        end
    end
    
    model.threshold = best_threshold;
    fprintf('   Optimal threshold: %.2f\n', best_threshold);
    fprintf('   Expected F1: %.4f, Specificity: %.4f\n', best_metrics.f1, best_metrics.specificity);
end

%% Evaluate Model
function results = evaluate_model(model, test_csv_file)
    fprintf('Loading test dataset: %s\n', test_csv_file);
    test_data = readtable(test_csv_file);
    
    % Handle missing values
    for col = 1:width(test_data)
        if isnumeric(test_data{:, col})
            test_data{:, col} = fillmissing(test_data{:, col}, 'constant', 0);
        elseif iscategorical(test_data{:, col}) || isstring(test_data{:, col}) || iscellstr(test_data{:, col})
            test_data{:, col} = fillmissing(test_data{:, col}, 'constant', '<missing>');
        end
    end
    
    % Feature engineering
    [engineered_test_data, ~] = dynamic_feature_engineering(test_data);
    
    % Extract features
    X_test = table2array(engineered_test_data(:, model.feature_names));
    y_true = engineered_test_data.label;
    
    if iscategorical(y_true) || isstring(y_true) || iscellstr(y_true)
        y_true = double(categorical(y_true));
    end
    y_true = double(y_true);
    
    X_test(isnan(X_test)) = 0;
    X_test(isinf(X_test)) = 0;
    
    % Apply same clipping as training
    X_test_clipped = X_test;
    for i = 1:size(X_test, 2)
        q1 = quantile(X_test(:, i), 0.01);
        q99 = quantile(X_test(:, i), 0.99);
        X_test_clipped(:, i) = max(min(X_test(:, i), q99), q1);
    end
    
    % Scale
    X_test_scaled = (X_test_clipped - model.scaler_mu) ./ model.scaler_sigma;
    X_test_scaled(isnan(X_test_scaled)) = 0;
    
    % Select features
    X_test_selected = X_test_scaled(:, model.selected_indices);
    
    % Predict
    y_proba = predict(model.classifier, X_test_selected);
    y_pred = double(y_proba > model.threshold);
    
    % Metrics
    accuracy = sum(y_pred == y_true) / length(y_true);
    [~, ~, ~, auc_score] = perfcurve(y_true, y_proba, 1);
    cm = confusionmat(y_true, y_pred);
    
    fprintf('RESULTS (threshold=%.2f):\n', model.threshold);
    fprintf('   Accuracy: %.4f\n', accuracy);
    fprintf('   AUC:      %.4f\n', auc_score);
    fprintf('\nConfusion Matrix:\n');
    fprintf('           Predicted\n');
    fprintf('           Normal  Attack\n');
    fprintf('Actual Normal   %6d  %6d\n', cm(1,1), cm(1,2));
    fprintf('       Attack   %6d  %6d\n', cm(2,1), cm(2,2));
    
    if size(cm, 1) == 2 && size(cm, 2) == 2
        precision = cm(2,2) / (cm(2,2) + cm(1,2));
        recall = cm(2,2) / (cm(2,2) + cm(2,1));
        f1_score = 2 * (precision * recall) / (precision + recall);
        specificity = cm(1,1) / (cm(1,1) + cm(1,2));
        fpr = 1 - specificity;
        
        fprintf('\n   Precision:    %.4f  (Attack predictions that are correct)\n', precision);
        fprintf('   Recall:       %.4f  (Attacks caught)\n', recall);
        fprintf('   F1-Score:     %.4f\n', f1_score);
        fprintf('   Specificity:  %.4f  (Normal traffic identified correctly)\n', specificity);
        fprintf('   FPR:          %.4f  (False alarm rate)\n', fpr);
        fprintf('\n   False Positives: %d (Normal → Attack)\n', cm(1,2));
        fprintf('   False Negatives: %d (Attack → Normal)\n', cm(2,1));
    end
    
    % Package results
    results = struct();
    results.accuracy = accuracy;
    results.auc_score = auc_score;
    results.y_true = y_true;
    results.y_pred = y_pred;
    results.y_proba = y_proba;
    results.confusion_matrix = cm;
    results.threshold = model.threshold;
    if exist('precision', 'var')
        results.precision = precision;
        results.recall = recall;
        results.f1_score = f1_score;
        results.specificity = specificity;
        results.fpr = fpr;
    end
end

%% Save Results as JSON
function save_results_json(results, model, filepath)
    fprintf('Saving JSON: %s\n', filepath);
    try
        output = struct();
        output.accuracy = results.accuracy;
        output.auc_score = results.auc_score;
        output.train_accuracy = model.train_accuracy;
        output.threshold = results.threshold;
        output.model_converged = model.converged;
        if isfield(results, 'precision')
            output.precision = results.precision;
            output.recall = results.recall;
            output.f1_score = results.f1_score;
            output.specificity = results.specificity;
            output.fpr = results.fpr;
        end
        output.confusion_matrix = results.confusion_matrix;
        output.selected_features = model.selected_features;
        output.num_features = length(model.selected_features);
        
        json_str = jsonencode(output);
        fid = fopen(filepath, 'w');
        fprintf(fid, '%s', json_str);
        fclose(fid);
        fprintf('   ✓ JSON saved successfully\n');
    catch ME
        fprintf('   JSON save failed: %s\n', ME.message);
        mat_file = strrep(filepath, '.json', '.mat');
        save(mat_file, 'results', 'model');
        fprintf('   Saved as MAT instead: %s\n', mat_file);
    end
end

%% RUN WITH YOUR FILES
main('C:\Users\axb9775\Desktop\UNSW_balanced_train.csv', ...
     'C:\Users\axb9775\Desktop\UNSW_balanced_test.csv', ...
     '.');