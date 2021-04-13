import torch
from torch.nn import Module, Linear, Softmax
from .modules import PreNet, CBHG

import hparams


class Net1(Module):
    def __init__(self, in_dims, train1_hidden_units, dropout_rate, num_conv1d_banks, num_highway_blocks):
        super().__init__()

        # in_dims = n_mfcc, out_dims_1 = 2*out_dims_2 = train1_hidden_units
        self.pre_net = PreNet(in_dims=in_dims,
                              out_dims_1=train1_hidden_units,
                              dropout_rate=dropout_rate)

        # num_conv1d_banks = train1_num_conv1d_banks, num_highway_blocks = train1_num_highway_blocks
        # in_dims = train1_hidden_units // 2, out_dims = train1_hidden_units // 2
        # activation=torch.nn.ReLU()
        self.cbhg = CBHG(num_conv1d_banks=num_conv1d_banks,
                         num_highway_blocks=num_highway_blocks,
                         in_dims=train1_hidden_units // 2,
                         out_dims=train1_hidden_units // 2,
                         activation=torch.nn.ReLU())

        # in_features = train1_hidden_units, out_features = phns_len
        self.logits = Linear(in_features=train1_hidden_units, out_features=hparams.phns_len)
        self.softmax = Softmax(dim=-1)

    def forward(self, inputs):
        # inputs : (N, L_in, in_dims)
        # in_dims = n_mfcc

        # PreNet
        pre_net_outputs = self.pre_net(inputs)
        # pre_net_outputs : (N, L_in, train1_hidden_units // 2)

        # change data format
        cbhg_inputs = pre_net_outputs.transpose(2, 1)
        # pre_net_outputs : (N, train1_hidden_units // 2, L_in)

        # CBHG
        cbhg_outputs = self.cbhg(cbhg_inputs)
        # cbhg_outputs : (N, L_in, train1_hidden_units)

        # Final linear projection
        logits_outputs = self.logits(cbhg_outputs)
        # logits_outputs : (N, L_in, phns_len)

        ppgs = self.softmax(logits_outputs / hparams.net1_train_logits_t)
        # ppgs : (N, L_in, phns_len)

        preds = torch.argmax(logits_outputs, dim=-1).int()
        # preds = (N, L_in)

        debug = True
        if debug:
            print("pre_net_outputs : " + str(pre_net_outputs.shape))
            print("cbhg_inputs : " + str(cbhg_inputs.shape))
            print("cbhg_outputs : " + str(cbhg_outputs.shape))
            print("logits_outputs : " + str(logits_outputs.shape))
            print("ppgs : " + str(ppgs.shape))
            print("preds : " + str(preds.shape) + " , preds.type : " + str(preds.dtype))

        # ppgs : (N, L_in, phns_len)
        # preds : (N, L_in)
        # logits_outputs : (N, L_in, phns_len)
        return ppgs, preds, logits_outputs
