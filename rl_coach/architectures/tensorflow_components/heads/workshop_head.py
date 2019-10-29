#
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import numpy as np
import tensorflow as tf

from rl_coach.architectures.tensorflow_components.layers import Dense
from rl_coach.architectures.tensorflow_components.heads.head import Head, normalized_columns_initializer
from rl_coach.base_parameters import AgentParameters
from rl_coach.core_types import ActionProbabilities
from rl_coach.exploration_policies.continuous_entropy import ContinuousEntropyParameters
from rl_coach.spaces import DiscreteActionSpace, BoxActionSpace, CompoundActionSpace
from rl_coach.spaces import SpacesDefinition
from rl_coach.utils import eps, indent_string


class WorkShopHead(Head):
    def __init__(self, agent_parameters: AgentParameters, spaces: SpacesDefinition, network_name: str,
                 head_idx: int = 0, loss_weight: float = 1., is_local: bool = True, activation_function: str='tanh',
                 dense_layer=Dense):
        super().__init__(agent_parameters, spaces, network_name, head_idx, loss_weight, is_local, activation_function,
                         dense_layer=dense_layer)
        self.name = 'workshop_head'
        self.return_type = ActionProbabilities


        self.exploration_policy = agent_parameters.exploration


    def _build_module(self, input_layer):
        self.actions = []
        self.input = self.actions
        self.policy_distributions = []
        self.output = []

        self._build_discrete_net(input_layer, self.spaces.action)

        if self.is_local:

            # calculate loss
            self.action_log_probs_wrt_policy = \
                tf.add_n([dist.log_prob(action) for dist, action in zip(self.policy_distributions, self.actions)])
            self.advantages = tf.placeholder(tf.float32, [None], name="advantages")
            self.target = self.advantages
            self.loss = -tf.reduce_mean(self.action_log_probs_wrt_policy * self.advantages)
            tf.losses.add_loss(self.loss_weight[0] * self.loss)

    def _build_discrete_net(self, input_layer, action_space):
        num_actions = len(action_space.actions)
        self.actions.append(tf.placeholder(tf.int32, [None], name="actions"))

        policy_values = self.dense_layer(num_actions)(input_layer, name='fc')
        self.policy_probs = tf.nn.softmax(policy_values, name="policy")

        # define the distributions for the policy and the old policy
        # (the + eps is to prevent probability 0 which will cause the log later on to be -inf)
        policy_distribution = tf.contrib.distributions.Categorical(probs=(self.policy_probs + eps))
        self.policy_distributions.append(policy_distribution)
        self.output.append(self.policy_probs)





    # def __str__(self):
    #     action_spaces = [self.spaces.action]
    #     if isinstance(self.spaces.action, CompoundActionSpace):
    #         action_spaces = self.spaces.action.sub_action_spaces
    #
    #     result = []
    #     for action_space_idx, action_space in enumerate(action_spaces):
    #         action_head_mean_result = []
    #         if isinstance(action_space, DiscreteActionSpace):
    #             # create a discrete action network (softmax probabilities output)
    #             action_head_mean_result.append("Dense (num outputs = {})".format(len(action_space.actions)))
    #             action_head_mean_result.append("Softmax")
    #         elif isinstance(action_space, BoxActionSpace):
    #             # create a continuous action network (bounded mean and stdev outputs)
    #             action_head_mean_result.append("Dense (num outputs = {})".format(action_space.shape))
    #             if np.all(action_space.max_abs_range < np.inf):
    #                 # bounded actions
    #                 action_head_mean_result.append("Activation (type = {})".format(self.activation_function.__name__))
    #                 action_head_mean_result.append("Multiply (factor = {})".format(action_space.max_abs_range))
    #
    #         action_head_stdev_result = []
    #         if isinstance(self.exploration_policy, ContinuousEntropyParameters):
    #             action_head_stdev_result.append("Dense (num outputs = {})".format(action_space.shape))
    #             action_head_stdev_result.append("Softplus")
    #
    #         action_head_result = []
    #         if action_head_stdev_result:
    #             action_head_result.append("Mean Stream")
    #             action_head_result.append(indent_string('\n'.join(action_head_mean_result)))
    #             action_head_result.append("Stdev Stream")
    #             action_head_result.append(indent_string('\n'.join(action_head_stdev_result)))
    #         else:
    #             action_head_result.append('\n'.join(action_head_mean_result))
    #
    #         if len(action_spaces) > 1:
    #             result.append("Action head {}".format(action_space_idx))
    #             result.append(indent_string('\n'.join(action_head_result)))
    #         else:
    #             result.append('\n'.join(action_head_result))
    #
    #     return '\n'.join(result)
