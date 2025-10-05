function results = train_decision_tree(csv_path, varargin)
% TRAIN_DECISION_TREE - Standalone Decision Tree Training in MATLAB
% Converted from Python standalone_decision_tree.py with exact same logic
%
% Usage:
%   results = train_decision_tree('data.csv')
%   results = train_decision_tree('data.csv', 'test_csv', 'test_data.csv')
%   results = train_decision_tree('data.csv', 'multiclass', true)
%   results = train_decision_tree('data.csv', 'use_sample', true)
%
% Parameters:
%   csv_path - Path to training dataset CSV file
%   'test_csv' - Path to test dataset CSV file (optional)
%   'multiclass' - Boolean for multi-class classification (default: false)
%   'use_sample' - Boolean to create sample data (default: false)
%
% Returns:
%   results - Structure containing accuracy, model, and other metrics

    % Parse input arguments
    p = inputParser;
    addRequired(p, 'csv_path', @ischar);
    addParameter(p, 'test_csv', '', @ischar);
    addParameter(p, 'multiclass', false, @islogical);
    addParameter(p, 'use_sample', false, @islogical);
    parse(p, csv_path, varargin{:});
    
    test_csv_path = p.Results.test_csv;
    classification_type = p.Results.multiclass;
    use_sample = p.Results.use_sample;
    
    fprintf('🌳 STANDALONE DECISION TREE TRAINING\n');
    fprintf('==================================================\n');
    if classification_type
        fprintf('🎯 CLASSIFICATION: MULTICLASS\n');
    else
        fprintf('🎯 CLASSIFICATION: BINARY\n');
    end
    fprintf('==================================================\n');
    
    % Create sample data if requested
    if use_sample
        fprintf('📊 Creating sample dataset for demonstration...\n');
        csv_path = create_sample_multiclass_data();
    end
    
    % Check if file exists
    if ~exist(csv_path, 'file')
        error('❌ Dataset not found: %s', csv_path);
    end
    
    % Load training data
    fprintf('📊 Loading training data...\n');
    data = readtable(csv_path);
    fprintf('✅ Dataset loaded: %d samples\n', height(data));
    
    % Check for attack category column for multiclass
    if classification_type
        if ~any(strcmp(data.Properties.VariableNames, 'attack_cat'))
            error('❌ No ''attack_cat'' column found in dataset\nMulti-class classification requires attack category labels');
        end
        
        % Show attack distribution
        [attack_types, ~, attack_idx] = unique(data.attack_cat);
        attack_counts = accumarray(attack_idx, 1);
        fprintf('📊 Attack types found: %d\n', length(attack_types));
        for i = 1:min(10, length(attack_types))
            fprintf('   %-15s: %6d samples\n', attack_types{i}, attack_counts(i));
        end
    end
    
    % Feature Engineering
    fprintf('\n🔧 FEATURE ENGINEERING\n');
    fprintf('------------------------------\n');
    data_engineered = apply_feature_engineering(data);
    
    % Preprocess data
    fprintf('📊 Preprocessing data...\n');
    [data_processed, label_encoders] = preprocess_data(data_engineered);
    
    % Determine target column and features
    if classification_type
        target_col = 'attack_cat';
        if any(strcmp(data_processed.Properties.VariableNames, target_col))
            [class_names, ~, y] = unique(data_processed.(target_col));
            y = y - 1; % Convert to 0-based indexing
        else
            error('Target column %s not found', target_col);
        end
    else
        if any(strcmp(data_processed.Properties.VariableNames, 'label'))
            target_col = 'label';
        elseif any(strcmp(data_processed.Properties.VariableNames, 'attack'))
            target_col = 'attack';
        else
            error('No suitable target column found (label or attack)');
        end
        y = data_processed.(target_col);
        class_names = {'Normal', 'Attack'};
    end
    
    % Select feature columns
    exclude_cols = {'attack_cat', 'label', 'attack', 'stime', 'srcip', 'dstip'};
    all_vars = data_processed.Properties.VariableNames;
    feature_cols = setdiff(all_vars, exclude_cols);
    
    % Extract feature matrix
    X = table2array(data_processed(:, feature_cols));
    
    % Handle missing values
    X(isnan(X)) = 0;
    X(isinf(X)) = 0;
    
    fprintf('📊 Features: %d\n', length(feature_cols));
    fprintf('📊 Samples: %d\n', size(X, 1));
    fprintf('📊 Classes: %d\n', length(unique(y)));
    
    % Scale features
    fprintf('\n🔧 SCALING FEATURES\n');
    fprintf('------------------------------\n');
    [X_scaled, mu, sigma] = zscore(X);
    
    % Handle any remaining NaN values from zscore
    X_scaled(isnan(X_scaled)) = 0;
    
    % Split data if no separate test set provided
    if isempty(test_csv_path)
        fprintf('\n✂️  SPLITTING DATA (70/30)\n');
        fprintf('------------------------------\n');
        cv = cvpartition(y, 'HoldOut', 0.3);
        X_train = X_scaled(training(cv), :);
        X_test = X_scaled(test(cv), :);
        y_train = y(training(cv));
        y_test = y(test(cv));
    else
        % Use separate test set
        fprintf('\n📊 Loading separate test data: %s\n', test_csv_path);
        test_data = readtable(test_csv_path);
        
        % Apply same preprocessing to test data
        test_data_engineered = apply_feature_engineering(test_data);
        test_data_processed = preprocess_data_transform(test_data_engineered, label_encoders);
        
        if classification_type
            [~, ~, y_test] = unique(test_data_processed.(target_col));
            y_test = y_test - 1;
        else
            if any(strcmp(test_data_processed.Properties.VariableNames, 'label'))
                test_target_col = 'label';
            else
                test_target_col = 'attack';
            end
            y_test = test_data_processed.(test_target_col);
        end
        
        X_test_raw = table2array(test_data_processed(:, feature_cols));
        X_test_raw(isnan(X_test_raw)) = 0;
        X_test_raw(isinf(X_test_raw)) = 0;
        
        % Apply same scaling
        X_test = (X_test_raw - mu) ./ sigma;
        X_test(isnan(X_test)) = 0;
        
        X_train = X_scaled;
        y_train = y;
    end
    
    fprintf('Training samples: %d\n', size(X_train, 1));
    fprintf('Test samples: %d\n', size(X_test, 1));
    
    % Train Decision Tree
    fprintf('\n🌳 TRAINING DECISION TREE\n');
    fprintf('------------------------------\n');
    fprintf('🚀 Training decision tree...\n');
    
    % Create decision tree with same parameters as Python version
    if classification_type
        dt_model = fitctree(X_train, y_train, ...
            'MaxNumSplits', 2^10-1, ...  % Equivalent to max_depth=10
            'MinLeafSize', 1, ...
            'MinParentSize', 2);
    else
        dt_model = fitctree(X_train, y_train, ...
            'MaxNumSplits', 2^10-1, ...
            'MinLeafSize', 1, ...
            'MinParentSize', 2);
    end
    
    % Make predictions
    fprintf('🔮 Making predictions...\n');
    y_pred = predict(dt_model, X_test);
    [~, y_proba] = predict(dt_model, X_test);
    
    % Calculate metrics
    accuracy = sum(y_pred == y_test) / length(y_test);
    
    fprintf('\n📊 RESULTS\n');
    fprintf('==============================\n');
    fprintf('🎯 Accuracy: %.4f\n', accuracy);
    
    % AUC for binary classification
    auc_score = NaN;
    if ~classification_type && length(unique(y)) == 2
        [~, ~, ~, auc_score] = perfcurve(y_test, y_proba(:, 2), 1);
        fprintf('📈 AUC Score: %.4f\n', auc_score);
    end
    
    % Classification report
    fprintf('\n📋 Classification Report:\n');
    if classification_type
        confmat = confusionmat(y_test, y_pred);
        fprintf('Confusion Matrix:\n');
        disp(confmat);
        
        % Calculate per-class metrics
        precision = diag(confmat) ./ sum(confmat, 1)';
        recall = diag(confmat) ./ sum(confmat, 2);
        f1_score = 2 * (precision .* recall) ./ (precision + recall);
        
        fprintf('\nPer-class metrics:\n');
        fprintf('%-15s %10s %10s %10s\n', 'Class', 'Precision', 'Recall', 'F1-Score');
        for i = 1:length(class_names)
            fprintf('%-15s %10.4f %10.4f %10.4f\n', class_names{i}, ...
                precision(i), recall(i), f1_score(i));
        end
    else
        confmat = confusionmat(y_test, y_pred);
        fprintf('Confusion Matrix:\n');
        disp(confmat);
        
        % Binary classification metrics
        TP = confmat(2, 2);
        TN = confmat(1, 1);
        FP = confmat(1, 2);
        FN = confmat(2, 1);
        
        precision = TP / (TP + FP);
        recall = TP / (TP + FN);
        f1_score = 2 * (precision * recall) / (precision + recall);
        
        fprintf('\nBinary classification metrics:\n');
        fprintf('Precision: %.4f\n', precision);
        fprintf('Recall: %.4f\n', recall);
        fprintf('F1-Score: %.4f\n', f1_score);
    end
    
    % Feature importance
    fprintf('\n🎯 TOP 10 MOST IMPORTANT FEATURES:\n');
    feature_importance = predictorImportance(dt_model);
    [sorted_importance, sort_idx] = sort(feature_importance, 'descend');
    
    for i = 1:min(10, length(feature_cols))
        fprintf('   %2d. %-25s %.4f\n', i, feature_cols{sort_idx(i)}, sorted_importance(i));
    end
    
    % Plot confusion matrix
    figure('Position', [100, 100, 800, 600]);
    confusionchart(y_test, y_pred, 'RowSummary', 'row-normalized', ...
        'ColumnSummary', 'column-normalized');
    title('Decision Tree - Confusion Matrix');
    saveas(gcf, 'decision_tree_confusion_matrix.png');
    
    % Feature importance plot
    figure('Position', [100, 100, 1000, 800]);
    top_n = min(15, length(feature_cols));
    barh(1:top_n, sorted_importance(1:top_n));
    set(gca, 'YTick', 1:top_n, 'YTickLabel', feature_cols(sort_idx(1:top_n)));
    xlabel('Feature Importance');
    title('Decision Tree - Top 15 Feature Importances');
    set(gca, 'YDir', 'reverse');
    grid on;
    saveas(gcf, 'decision_tree_feature_importance.png');
    
    % Save the trained model
    model_data.classifier = dt_model;
    model_data.scaler_mu = mu;
    model_data.scaler_sigma = sigma;
    model_data.label_encoders = label_encoders;
    model_data.feature_names = feature_cols;
    model_data.class_names = class_names;
    model_data.classification_type = classification_type;
    
    save('trained_decision_tree_model.mat', 'model_data');
    
    fprintf('\n💾 Model saved as: trained_decision_tree_model.mat\n');
    fprintf('📁 Generated files:\n');
    fprintf('   - decision_tree_confusion_matrix.png\n');
    fprintf('   - decision_tree_feature_importance.png\n');
    
    % Return results
    results.accuracy = accuracy;
    results.auc_score = auc_score;
    results.model = dt_model;
    results.confusion_matrix = confmat;
    results.feature_importance = sorted_importance;
    results.feature_names = feature_cols(sort_idx);
    
    fprintf('\n🎉 DECISION TREE TRAINING COMPLETE!\n');
    fprintf('========================================\n');
    fprintf('🎯 Final Accuracy: %.4f\n', accuracy);
    if ~isnan(auc_score)
        fprintf('📈 AUC Score: %.4f\n', auc_score);
    end
    
    fprintf('\n💡 To use the trained model:\n');
    fprintf('   Load ''trained_decision_tree_model.mat''\n');
    fprintf('   Apply same preprocessing pipeline to new data\n');
end

function data_engineered = apply_feature_engineering(data)
    % Apply feature engineering following the same logic as Python version
    
    fprintf('🔧 Creating temporal features...\n');
    data_engineered = create_temporal_features(data);
    
    fprintf('🔧 Creating statistical features...\n');
    data_engineered = create_statistical_features(data_engineered);
    
    fprintf('🔧 Creating interaction features...\n');
    data_engineered = create_interaction_features(data_engineered);
    
    fprintf('🔧 Creating network behavior features...\n');
    data_engineered = create_network_behavior_features(data_engineered);
    
    fprintf('✅ Feature engineering completed\n');
end

function data = create_temporal_features(data)
    % Create time-based features from network flows
    
    if any(strcmp(data.Properties.VariableNames, 'stime'))
        % Convert to datetime
        stime_dt = datetime(data.stime, 'ConvertFrom', 'posixtime');
        
        % Time-based features
        data.hour = hour(stime_dt);
        data.day_of_week = weekday(stime_dt) - 1; % Convert to 0-6 like Python
        data.is_weekend = double(data.day_of_week >= 5);
        data.is_business_hours = double(data.hour >= 9 & data.hour <= 17);
        data.is_night = double(data.hour >= 22 | data.hour <= 6);
    end
end

function data = create_statistical_features(data)
    % Create advanced statistical features
    
    % Byte-related ratios and statistics
    if any(strcmp(data.Properties.VariableNames, 'sbytes')) && ...
       any(strcmp(data.Properties.VariableNames, 'dbytes'))
        data.total_bytes = data.sbytes + data.dbytes;
        data.byte_ratio = data.sbytes ./ max(data.dbytes, 1); % Avoid division by zero
        data.byte_ratio(data.dbytes == 0) = 0;
        data.byte_imbalance = abs(data.sbytes - data.dbytes);
        data.log_total_bytes = log1p(data.total_bytes);
    end
    
    % Packet-related features
    if any(strcmp(data.Properties.VariableNames, 'spkts')) && ...
       any(strcmp(data.Properties.VariableNames, 'dpkts'))
        data.total_packets = data.spkts + data.dpkts;
        data.packet_ratio = data.spkts ./ max(data.dpkts, 1);
        data.packet_ratio(data.dpkts == 0) = 0;
        
        if any(strcmp(data.Properties.VariableNames, 'total_bytes'))
            data.avg_packet_size = data.total_bytes ./ max(data.total_packets, 1);
            data.avg_packet_size(data.total_packets == 0) = 0;
        end
    end
    
    % Duration-based features
    if any(strcmp(data.Properties.VariableNames, 'dur'))
        data.log_duration = log1p(data.dur);
        data.is_short_connection = double(data.dur < 1);
        data.is_long_connection = double(data.dur > 300);
        
        % Throughput features
        if any(strcmp(data.Properties.VariableNames, 'total_bytes'))
            data.throughput = data.total_bytes ./ max(data.dur, 0.001);
            data.throughput(data.dur == 0) = 0;
            data.log_throughput = log1p(data.throughput);
        end
    end
    
    % Port-based features
    if any(strcmp(data.Properties.VariableNames, 'sport')) && ...
       any(strcmp(data.Properties.VariableNames, 'dport'))
        data.src_is_wellknown = double(data.sport < 1024);
        data.dst_is_wellknown = double(data.dport < 1024);
        data.port_difference = abs(data.sport - data.dport);
        
        % Common service ports
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995];
        data.dst_is_common_service = double(ismember(data.dport, common_ports));
    end
end

function data = create_interaction_features(data)
    % Create interaction features between important variables
    
    % Protocol-service interactions
    if any(strcmp(data.Properties.VariableNames, 'proto')) && ...
       any(strcmp(data.Properties.VariableNames, 'service'))
        proto_service_combo = strcat(string(data.proto), '_', string(data.service));
        [~, ~, data.proto_service_encoded] = unique(proto_service_combo);
        data.proto_service_encoded = data.proto_service_encoded - 1; % 0-based
    end
    
    % State-protocol interactions
    if any(strcmp(data.Properties.VariableNames, 'state')) && ...
       any(strcmp(data.Properties.VariableNames, 'proto'))
        state_proto_combo = strcat(string(data.state), '_', string(data.proto));
        [~, ~, data.state_proto_encoded] = unique(state_proto_combo);
        data.state_proto_encoded = data.state_proto_encoded - 1; % 0-based
    end
end

function data = create_network_behavior_features(data)
    % Create features that capture network behavior patterns
    
    % Loss and jitter patterns
    if any(strcmp(data.Properties.VariableNames, 'sloss')) && ...
       any(strcmp(data.Properties.VariableNames, 'dloss'))
        data.total_loss = data.sloss + data.dloss;
        data.loss_ratio = data.sloss ./ max(data.dloss, 1);
        data.loss_ratio(data.dloss == 0) = 0;
        data.has_loss = double(data.total_loss > 0);
    end
    
    if any(strcmp(data.Properties.VariableNames, 'sjit')) && ...
       any(strcmp(data.Properties.VariableNames, 'djit'))
        data.total_jitter = data.sjit + data.djit;
        data.jitter_ratio = data.sjit ./ max(data.djit, 1);
        data.jitter_ratio(data.djit == 0) = 0;
        jitter_threshold = quantile(data.total_jitter, 0.9);
        data.high_jitter = double(data.total_jitter > jitter_threshold);
    end
    
    % Window size patterns
    if any(strcmp(data.Properties.VariableNames, 'swin')) && ...
       any(strcmp(data.Properties.VariableNames, 'dwin'))
        data.window_ratio = data.swin ./ max(data.dwin, 1);
        data.window_ratio(data.dwin == 0) = 0;
        data.min_window = min(data.swin, data.dwin);
        data.max_window = max(data.swin, data.dwin);
    end
end

function [data_processed, label_encoders] = preprocess_data(data)
    % Complete data preprocessing pipeline
    
    % Handle missing values
    data_processed = data;
    numeric_vars = varfun(@isnumeric, data_processed, 'output', 'uniform');
    numeric_var_names = data_processed.Properties.VariableNames(numeric_vars);
    
    for i = 1:length(numeric_var_names)
        var_name = numeric_var_names{i};
        data_processed.(var_name)(isnan(data_processed.(var_name))) = 0;
        data_processed.(var_name)(isinf(data_processed.(var_name))) = 0;
    end
    
    % Encode categorical variables
    categorical_cols = {'proto', 'service', 'state'};
    label_encoders = struct();
    
    for i = 1:length(categorical_cols)
        col = categorical_cols{i};
        if any(strcmp(data_processed.Properties.VariableNames, col))
            [unique_vals, ~, encoded_vals] = unique(data_processed.(col));
            label_encoders.(col) = unique_vals;
            data_processed.(col) = encoded_vals - 1; % 0-based indexing
        end
    end
end

function data_processed = preprocess_data_transform(data, label_encoders)
    % Apply same preprocessing without fitting encoders
    
    % Handle missing values
    data_processed = data;
    numeric_vars = varfun(@isnumeric, data_processed, 'output', 'uniform');
    numeric_var_names = data_processed.Properties.VariableNames(numeric_vars);
    
    for i = 1:length(numeric_var_names)
        var_name = numeric_var_names{i};
        data_processed.(var_name)(isnan(data_processed.(var_name))) = 0;
        data_processed.(var_name)(isinf(data_processed.(var_name))) = 0;
    end
    
    % Apply existing encoders
    categorical_cols = fieldnames(label_encoders);
    for i = 1:length(categorical_cols)
        col = categorical_cols{i};
        if any(strcmp(data_processed.Properties.VariableNames, col))
            unique_vals = label_encoders.(col);
            [~, encoded_vals] = ismember(data_processed.(col), unique_vals);
            encoded_vals(encoded_vals == 0) = 1; % Handle unseen values
            data_processed.(col) = encoded_vals - 1; % 0-based indexing
        end
    end
end

function csv_path = create_sample_multiclass_data()
    % Create sample data with multiple attack types for testing
    
    fprintf('🔧 Creating sample multi-class data...\n');
    
    rng(42); % Set random seed for reproducibility
    n_samples = 1000;
    
    % Define attack types
    attack_types = {'Normal', 'DoS', 'Exploits', 'Fuzzers', 'Generic', 'Reconnaissance'};
    attack_probs = [0.5, 0.1, 0.15, 0.1, 0.1, 0.05];
    
    % Generate sample network features
    data = table();
    
    % Generate IP addresses
    srcip = cell(n_samples, 1);
    dstip = cell(n_samples, 1);
    for i = 1:n_samples
        srcip{i} = sprintf('192.168.%d.%d', randi(255), randi(255));
        dstip{i} = sprintf('10.0.%d.%d', randi(255), randi(255));
    end
    data.srcip = srcip;
    data.dstip = dstip;
    
    % Generate other features
    data.sport = randi([1024, 65535], n_samples, 1);
    data.dport = randi([1, 65535], n_samples, 1);
    
    proto_options = {'tcp', 'udp', 'icmp'};
    data.proto = proto_options(randi(3, n_samples, 1))';
    
    service_options = {'http', 'https', 'ftp', 'ssh', 'dns'};
    data.service = service_options(randi(5, n_samples, 1))';
    
    state_options = {'CON', 'FIN', 'RST', 'REQ'};
    data.state = state_options(randi(4, n_samples, 1))';
    
    data.dur = exprnd(2.0, n_samples, 1);
    data.sbytes = round(exprnd(1000, n_samples, 1));
    data.dbytes = round(exprnd(1000, n_samples, 1));
    data.sttl = randi([32, 255], n_samples, 1);
    data.dttl = randi([32, 255], n_samples, 1);
    data.sloss = poissrnd(0.1, n_samples, 1);
    data.dloss = poissrnd(0.1, n_samples, 1);
    data.sinpkt = exprnd(10, n_samples, 1);
    data.dinpkt = exprnd(10, n_samples, 1);
    data.sjit = exprnd(0.1, n_samples, 1);
    data.djit = exprnd(0.1, n_samples, 1);
    data.swin = randi([1024, 65535], n_samples, 1);
    data.dwin = randi([1024, 65535], n_samples, 1);
    data.tcprtt = exprnd(0.05, n_samples, 1);
    data.synack = exprnd(0.01, n_samples, 1);
    data.ackdat = exprnd(0.01, n_samples, 1);
    data.smean = exprnd(100, n_samples, 1);
    data.dmean = exprnd(100, n_samples, 1);
    data.trans_depth = randi([0, 10], n_samples, 1);
    data.response_body_len = round(exprnd(500, n_samples, 1));
    data.spkts = poissrnd(5, n_samples, 1);
    data.dpkts = poissrnd(5, n_samples, 1);
    data.stime = 1600000000 + rand(n_samples, 1) * 86400; % Random times in a day
    
    % Assign attack categories
    attack_indices = randsample(1:length(attack_types), n_samples, true, attack_probs);
    data.attack_cat = attack_types(attack_indices)';
    
    % Create binary labels
    data.label = double(~strcmp(data.attack_cat, 'Normal'));
    
    % Save to CSV
    csv_path = 'sample_multiclass_data.csv';
    writetable(data, csv_path);
    
    fprintf('✅ Created sample multi-class data: %d samples\n', n_samples);
    fprintf('📊 Attack distribution:\n');
    [unique_attacks, ~, attack_idx] = unique(data.attack_cat);
    attack_counts = accumarray(attack_idx, 1);
    for i = 1:length(unique_attacks)
        fprintf('   %-15s: %4d samples\n', unique_attacks{i}, attack_counts(i));
    end
end